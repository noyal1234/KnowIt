protocol AuthRepositoryProtocol: Sendable {
    func login(email: String, password: String) async throws -> User
    func register(email: String, password: String, displayName: String) async throws -> User
    func fetchCurrentUser() async throws -> User
    func refreshSession() async throws
    func logout() async throws
    var isLoggedIn: Bool { get }
}
