import Foundation

@Observable
@MainActor
final class HomeViewModel {
    let user: User
    private(set) var state: ViewState<String> = .loaded("ready")

    private let onLogout: () -> Void

    init(user: User, onLogout: @escaping () -> Void) {
        self.user = user
        self.onLogout = onLogout
    }

    func logoutTapped() {
        onLogout()
    }
}
