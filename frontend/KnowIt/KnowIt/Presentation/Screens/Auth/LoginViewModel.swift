import Foundation

@Observable
@MainActor
final class LoginViewModel {
    var email = ""
    var password = ""
    private(set) var state: ViewState<User> = .idle

    private let loginUseCase: LoginUseCase
    private let onSuccess: () -> Void

    init(loginUseCase: LoginUseCase, onSuccess: @escaping () -> Void) {
        self.loginUseCase = loginUseCase
        self.onSuccess = onSuccess
    }

    func login() async {
        guard !email.isEmpty, !password.isEmpty else {
            state = .error(AppError(message: "Email and password are required.", isRetryable: false))
            return
        }
        state = .loading
        do {
            let user = try await loginUseCase.execute(email: email, password: password)
            state = .loaded(user)
            onSuccess()
        } catch {
            state = .error(AppError.from(error))
        }
    }

    static func preview(state: ViewState<User> = .idle) -> LoginViewModel {
        let vm = LoginViewModel(loginUseCase: LoginUseCase(repository: PreviewAuthRepository()), onSuccess: {})
        vm.state = state
        return vm
    }
}

private struct PreviewAuthRepository: AuthRepositoryProtocol {
    var isLoggedIn: Bool { false }
    func login(email: String, password: String) async throws -> User {
        User(id: UUID(), email: email, displayName: "Preview", region: "US")
    }
    func register(email: String, password: String, displayName: String) async throws -> User {
        User(id: UUID(), email: email, displayName: displayName, region: "US")
    }
    func fetchCurrentUser() async throws -> User {
        User(id: UUID(), email: "preview@knowit.app", displayName: "Preview", region: "US")
    }
    func refreshSession() async throws {}
    func logout() async throws {}
}
