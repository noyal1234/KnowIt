import Foundation

@Observable
@MainActor
final class RegisterViewModel {
    var email = ""
    var password = ""
    var displayName = ""
    private(set) var state: ViewState<User> = .idle

    private let registerUseCase: RegisterUseCase
    private let onSuccess: () -> Void

    init(registerUseCase: RegisterUseCase, onSuccess: @escaping () -> Void) {
        self.registerUseCase = registerUseCase
        self.onSuccess = onSuccess
    }

    func register() async {
        guard !email.isEmpty, password.count >= 8 else {
            state = .error(AppError(
                message: "Enter a valid email and password (min 8 characters).",
                isRetryable: false
            ))
            return
        }
        state = .loading
        do {
            let user = try await registerUseCase.execute(
                email: email,
                password: password,
                displayName: displayName
            )
            state = .loaded(user)
            onSuccess()
        } catch {
            state = .error(AppError.from(error))
        }
    }
}
