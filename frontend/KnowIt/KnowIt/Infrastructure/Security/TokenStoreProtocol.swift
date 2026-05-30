import Foundation

protocol TokenStoreProtocol: Sendable {
    var refreshHandler: (@Sendable () async throws -> Void)? { get set }

    func validAccessToken() async throws -> String
    func save(accessToken: String, refreshToken: String)
    func token() -> StoredToken
    func clearTokens()
}
