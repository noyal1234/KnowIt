import SwiftUI

struct HomeView: View {
    @State private var viewModel: HomeViewModel
    @State private var showServerConfig = false

    init(viewModel: HomeViewModel) {
        _viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: AppSpacing.l) {
                Text("Hello, \(viewModel.user.displayName)")
                    .font(AppTypography.headingMedium)

                Text(String(localized: "home.subtitle"))
                    .font(AppTypography.body)
                    .foregroundStyle(AppColor.textSecondary)

                VStack(alignment: .leading, spacing: AppSpacing.s) {
                    Label(String(localized: "home.scan.placeholder"), systemImage: "barcode.viewfinder")
                    Label(String(localized: "home.dashboard.placeholder"), systemImage: "chart.bar.fill")
                }
                .font(AppTypography.bodySmall)
                .padding(AppSpacing.m)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(AppColor.surfaceCard)
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.card))

                Spacer()
            }
            .padding(AppSpacing.screenHorizontal)
            .background(AppColor.surfaceBackground)
            .navigationTitle("KnowIt")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    #if DEBUG
                    Button(String(localized: "devtools.server")) {
                        showServerConfig = true
                    }
                    #endif
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(String(localized: "auth.logout")) {
                        viewModel.logoutTapped()
                    }
                }
            }
            .sheet(isPresented: $showServerConfig) {
                NavigationStack {
                    ServerConfigView()
                }
            }
        }
    }
}

#Preview {
    HomeView(
        viewModel: HomeViewModel(
            user: User(id: UUID(), email: "demo@knowit.app", displayName: "Demo", region: "US"),
            onLogout: {}
        )
    )
}
