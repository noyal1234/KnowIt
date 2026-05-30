final class AuthRepository: AuthRepositoryProtocol, @unchecked Sendable {
    private let remote: AuthRemoteDataSource
    private let tokenStore: TokenStoreProtocol

    init(remote: AuthRemoteDataSource, tokenStore: TokenStoreProtocol) {
        self.remote = remote
        self.tokenStore = tokenStore
    }

    var isLoggedIn: Bool {
        tokenStore.token().isLoggedIn
    }

    func login(email: String, password: String) async throws -> User {
        do {
            let dto = try await remote.login(email: email, password: password)
            let tokens = AuthMapper.toTokens(from: dto)
            tokenStore.save(accessToken: tokens.accessToken, refreshToken: tokens.refreshToken)
            return try await fetchCurrentUser()
        } catch let error as NetworkError {
            if case .unauthorized = error { throw AuthError.invalidCredentials }
            throw AuthError.network(underlying: error)
        }
    }

    func register(email: String, password: String, displayName: String) async throws -> User {
        do {
            let dto = try await remote.register(email: email, password: password, displayName: displayName)
            let tokens = AuthMapper.toTokens(from: dto)
            tokenStore.save(accessToken: tokens.accessToken, refreshToken: tokens.refreshToken)
            return try await fetchCurrentUser()
        } catch let error as NetworkError {
            throw AuthError.network(underlying: error)
        }
    }

    func fetchCurrentUser() async throws -> User {
        do {
            let dto = try await remote.fetchMe()
            return AuthMapper.toUser(from: dto)
        } catch let error as NetworkError {
            if case .unauthorized = error { throw AuthError.sessionExpired }
            throw AuthError.network(underlying: error)
        }
    }

    func refreshSession() async throws {
        let refresh = tokenStore.token().refreshToken
        guard !refresh.isEmpty else { throw AuthError.sessionExpired }
        let dto = try await remote.refresh(refreshToken: refresh)
        let tokens = AuthMapper.toTokens(from: dto)
        tokenStore.save(accessToken: tokens.accessToken, refreshToken: tokens.refreshToken)
    }

    func logout() async throws {
        let refresh = tokenStore.token().refreshToken
        if !refresh.isEmpty {
            try? await remote.logout(refreshToken: refresh)
        }
        tokenStore.clearTokens()
    }
}
