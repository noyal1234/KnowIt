import Foundation

nonisolated struct User: Sendable, Equatable, Identifiable {
    let id: UUID
    let email: String
    let displayName: String
    let region: String
}

nonisolated struct AuthTokens: Sendable, Equatable {
    let accessToken: String
    let refreshToken: String
}
