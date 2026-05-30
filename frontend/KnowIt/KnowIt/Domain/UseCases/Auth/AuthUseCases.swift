nonisolated struct LoginUseCase: Sendable {
    private let repository: AuthRepositoryProtocol

    init(repository: AuthRepositoryProtocol) {
        self.repository = repository
    }

    func execute(email: String, password: String) async throws -> User {
        try await repository.login(email: email, password: password)
    }
}

nonisolated struct RegisterUseCase: Sendable {
    private let repository: AuthRepositoryProtocol

    init(repository: AuthRepositoryProtocol) {
        self.repository = repository
    }

    func execute(email: String, password: String, displayName: String) async throws -> User {
        try await repository.register(email: email, password: password, displayName: displayName)
    }
}

nonisolated struct FetchCurrentUserUseCase: Sendable {
    private let repository: AuthRepositoryProtocol

    init(repository: AuthRepositoryProtocol) {
        self.repository = repository
    }

    func execute() async throws -> User {
        try await repository.fetchCurrentUser()
    }
}

nonisolated struct LogoutUseCase: Sendable {
    private let repository: AuthRepositoryProtocol

    init(repository: AuthRepositoryProtocol) {
        self.repository = repository
    }

    func execute() async throws {
        try await repository.logout()
    }
}
