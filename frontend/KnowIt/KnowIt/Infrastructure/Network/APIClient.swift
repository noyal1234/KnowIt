import Foundation
import OSLog

protocol APIClientProtocol: Sendable {
    func request<T: Decodable & Sendable>(_ endpoint: APIEndpoint) async throws -> T
    func requestEmpty(_ endpoint: APIEndpoint) async throws
}

nonisolated final class APIClient: APIClientProtocol {
    private let session: URLSession
    private let baseURL: URL
    private let tokenStore: TokenStoreProtocol
    private let requestBuilder: RequestBuilderProtocol
    private let decoder: JSONDecoder

    init(
        session: URLSession = URLSession(configuration: .knowItDefault),
        baseURL: URL = AppConfig.apiBaseURL,
        tokenStore: TokenStoreProtocol,
        requestBuilder: RequestBuilderProtocol = RequestBuilder()
    ) {
        self.session = session
        self.baseURL = baseURL
        self.tokenStore = tokenStore
        self.requestBuilder = requestBuilder
        self.decoder = .apiDecoder
    }

    func request<T: Decodable & Sendable>(_ endpoint: APIEndpoint) async throws -> T {
        let urlRequest = try await requestBuilder.build(endpoint, baseURL: baseURL, tokenStore: tokenStore)
        let data = try await executeWithRetry(urlRequest, policy: endpoint.retryPolicy, path: endpoint.path)
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            AppLogger.network.error("event=DecodingFailed path=\(endpoint.path, privacy: .public)")
            throw NetworkError.decodingFailed(error)
        }
    }

    func requestEmpty(_ endpoint: APIEndpoint) async throws {
        let urlRequest = try await requestBuilder.build(endpoint, baseURL: baseURL, tokenStore: tokenStore)
        _ = try await executeWithRetry(urlRequest, policy: endpoint.retryPolicy, path: endpoint.path)
    }

    private func executeWithRetry(
        _ request: URLRequest,
        policy: RetryPolicy,
        path: String
    ) async throws -> Data {
        var attempt = 0
        let maxAttempts = policy.maxAttempts
        var lastError: Error?

        while attempt < maxAttempts {
            do {
                let (data, response) = try await session.data(for: request)
                guard let http = response as? HTTPURLResponse else {
                    throw NetworkError.serverError(statusCode: -1)
                }
                let result = try mapHTTPResponse(http, data: data)
                AppLogger.network.info(
                    "event=RequestSucceeded path=\(path, privacy: .public) status=\(http.statusCode, privacy: .public)"
                )
                return result
            } catch NetworkError.unauthorized {
                throw NetworkError.unauthorized
            } catch NetworkError.forbidden {
                throw NetworkError.forbidden
            } catch {
                lastError = error
                attempt += 1
                if attempt >= maxAttempts { break }
                let delay = policy.delay(forAttempt: attempt)
                AppLogger.network.warning(
                    "event=RequestRetry path=\(path, privacy: .public) attempt=\(attempt, privacy: .public)"
                )
                try await Task.sleep(for: .seconds(delay))
            }
        }

        throw lastError ?? NetworkError.serverError(statusCode: -1)
    }

    private func mapHTTPResponse(_ response: HTTPURLResponse, data: Data) throws -> Data {
        switch response.statusCode {
        case 200...299:
            return data
        case 401:
            throw NetworkError.unauthorized
        case 403:
            throw NetworkError.forbidden
        case 404:
            throw NetworkError.notFound
        case 409:
            throw NetworkError.conflict
        case 500...599:
            throw NetworkError.serverError(statusCode: response.statusCode)
        default:
            throw NetworkError.serverError(statusCode: response.statusCode)
        }
    }
}
