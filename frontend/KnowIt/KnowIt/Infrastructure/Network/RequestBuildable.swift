import Foundation

protocol RequestBuildable {
    var path: String { get }
    var method: HTTPMethod { get }
    var body: Encodable? { get }
    var queryItems: [URLQueryItem]? { get }
    var timeout: TimeInterval { get }
    var retryPolicy: RetryPolicy { get }
    var requiresAuth: Bool { get }
}

extension RequestBuildable {
    var queryItems: [URLQueryItem]? { nil }
    var body: Encodable? { nil }
    var timeout: TimeInterval { 30 }
    var retryPolicy: RetryPolicy { .exponential(maxAttempts: 3) }
}
