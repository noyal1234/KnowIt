import SwiftUI

struct RootView: View {
    @State private var viewModel: RootViewModel
    private let assembler: AppAssembler

    init(viewModel: RootViewModel, assembler: AppAssembler) {
        _viewModel = State(initialValue: viewModel)
        self.assembler = assembler
    }

    var body: some View {
        Group {
            switch viewModel.phase {
            case .bootstrapping:
                ProgressView(String(localized: "root.loading"))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(AppColor.surfaceBackground)
            case .unauthenticated:
                NavigationStack {
                    LoginView(
                        viewModel: assembler.makeLoginViewModel {
                            Task { await refreshSession() }
                        }
                    )
                    .navigationDestination(for: AppRoute.self) { route in
                        switch route {
                        case .register:
                            RegisterView(
                                viewModel: assembler.makeRegisterViewModel {
                                    Task { await refreshSession() }
                                }
                            )
                        default:
                            EmptyView()
                        }
                    }
                }
            case .authenticated(let user):
                HomeView(
                    viewModel: assembler.makeHomeViewModel(user: user) {
                        Task { await handleLogout() }
                    }
                )
            }
        }
        .task { await viewModel.resolveInitialRoute() }
        .onReceive(NotificationCenter.default.publisher(for: .knowItSessionExpired)) { _ in
            viewModel.markLoggedOut()
        }
    }

    private func refreshSession() async {
        await viewModel.resolveInitialRoute()
    }

    private func handleLogout() async {
        do {
            try await assembler.logoutUseCase.execute()
        } catch {
            AppLogger.auth.warning("event=LogoutFailed")
        }
        viewModel.markLoggedOut()
    }
}

#Preview {
    RootView(viewModel: AppAssembler.preview.rootViewModel, assembler: .preview)
}
