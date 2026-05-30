nonisolated final class AuthRemoteDataSource: Sendable {
    private let apiClient: APIClientProtocol

    init(apiClient: APIClientProtocol) {
        self.apiClient = apiClient
    }

    func login(email: String, password: String) async throws -> TokenResponseDTO {
        try await apiClient.request(.login(email: email, password: password))
    }

    func register(email: String, password: String, displayName: String) async throws -> TokenResponseDTO {
        try await apiClient.request(.register(email: email, password: password, displayName: displayName))
    }

    func refresh(refreshToken: String) async throws -> TokenResponseDTO {
        try await apiClient.request(.refreshToken(refreshToken: refreshToken))
    }

    func logout(refreshToken: String) async throws {
        try await apiClient.requestEmpty(.logout(refreshToken: refreshToken))
    }

    func fetchMe() async throws -> UserDTO {
        try await apiClient.request(.me)
    }
}
