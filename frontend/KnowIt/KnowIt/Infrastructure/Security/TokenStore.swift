import Foundation

extension Notification.Name {
    static let knowItSessionExpired = Notification.Name("com.knowit.sessionExpired")
    static let knowItAuthStateChanged = Notification.Name("com.knowit.authStateChanged")
}

final class TokenStore: TokenStoreProtocol, @unchecked Sendable {
    var refreshHandler: (@Sendable () async throws -> Void)?

    func validAccessToken() async throws -> String {
        let stored = token()
        if !stored.accessToken.isEmpty {
            return stored.accessToken
        }
        guard !stored.refreshToken.isEmpty else {
            throw AuthError.sessionExpired
        }
        try await refreshHandler?()
        let refreshed = token()
        guard !refreshed.accessToken.isEmpty else {
            throw AuthError.sessionExpired
        }
        return refreshed.accessToken
    }

    func save(accessToken: String, refreshToken: String) {
        KeychainHelper.save(accessToken, forKey: KeychainKeys.accessToken)
        KeychainHelper.save(refreshToken, forKey: KeychainKeys.refreshToken)
        AppLogger.auth.info("event=TokenSaved")
        NotificationCenter.default.post(name: .knowItAuthStateChanged, object: nil)
    }

    func token() -> StoredToken {
        StoredToken(
            accessToken: KeychainHelper.read(forKey: KeychainKeys.accessToken) ?? "",
            refreshToken: KeychainHelper.read(forKey: KeychainKeys.refreshToken) ?? ""
        )
    }

    func clearTokens() {
        KeychainHelper.delete(forKey: KeychainKeys.accessToken)
        KeychainHelper.delete(forKey: KeychainKeys.refreshToken)
        AppLogger.auth.info("event=TokensCleared")
        NotificationCenter.default.post(name: .knowItSessionExpired, object: nil)
        NotificationCenter.default.post(name: .knowItAuthStateChanged, object: nil)
    }
}
