import Foundation

protocol RequestBuilderProtocol: Sendable {
    func build(
        _ endpoint: APIEndpoint,
        baseURL: URL,
        tokenStore: TokenStoreProtocol
    ) async throws -> URLRequest
}

nonisolated final class RequestBuilder: RequestBuilderProtocol {
    func build(
        _ endpoint: APIEndpoint,
        baseURL: URL,
        tokenStore: TokenStoreProtocol
    ) async throws -> URLRequest {
        let base = baseURL.absoluteString.hasSuffix("/")
            ? String(baseURL.absoluteString.dropLast())
            : baseURL.absoluteString
        let pathComponent = endpoint.path.hasPrefix("/") ? endpoint.path : "/\(endpoint.path)"
        guard let initialURL = URL(string: base + pathComponent) else {
            throw NetworkError.invalidURL(endpoint.path)
        }

        let url: URL
        if let items = endpoint.queryItems, !items.isEmpty {
            var components = URLComponents(url: initialURL, resolvingAgainstBaseURL: false)
            components?.queryItems = items
            guard let built = components?.url else { throw NetworkError.invalidURL(endpoint.path) }
            url = built
        } else {
            url = initialURL
        }

        var request = URLRequest(url: url, timeoutInterval: endpoint.timeout)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue(AppConfig.appVersion, forHTTPHeaderField: "X-App-Version")
        request.setValue(AppConfig.platform, forHTTPHeaderField: "X-Platform")

        if endpoint.requiresAuth {
            let token = try await tokenStore.validAccessToken()
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = endpoint.body {
            do {
                request.httpBody = try JSONEncoder.apiEncoder.encode(AnyEncodable(body))
            } catch {
                throw NetworkError.encodingFailed(error)
            }
        }

        return request
    }
}

/// Type-erased Encodable wrapper for heterogeneous endpoint bodies.
private nonisolated struct AnyEncodable: Encodable {
    private let encode: (Encoder) throws -> Void

    init(_ wrapped: Encodable) {
        encode = wrapped.encode
    }

    func encode(to encoder: Encoder) throws {
        try encode(encoder)
    }
}
