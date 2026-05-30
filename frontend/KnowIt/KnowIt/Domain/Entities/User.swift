import Foundation

struct User: Sendable, Equatable, Identifiable {
    let id: UUID
    let email: String
    let displayName: String
    let region: String
}

struct AuthTokens: Sendable, Equatable {
    let accessToken: String
    let refreshToken: String
}
