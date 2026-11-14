import { Link } from "react-router-dom";
import { GapNotice } from "../../components/ui/feedback";

interface Props {
  title: string;
  intro: string;
  gapTitle: string;
  gap: string;
}

function FeatureGap({ title, intro, gapTitle, gap }: Props) {
  return (
    <div className="card space-y-5 p-6 sm:p-8">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-ink/60">{intro}</p>
      </div>
      <GapNotice title={gapTitle}>{gap}</GapNotice>
      <Link to="/signin" className="inline-block text-sm font-semibold text-brand-700 hover:underline">
        Back to sign in
      </Link>
    </div>
  );
}

export const ForgotPassword = () => (
  <FeatureGap
    title="Reset your password"
    intro="Password recovery isn't available yet."
    gapTitle="password recovery"
    gap="The auth service has change-password for signed-in users only. A request-reset and confirm-reset endpoint pair (plus the email from the notification service) is needed before this form can be built."
  />
);

export const VerifyAccount = () => (
  <FeatureGap
    title="Verify your account"
    intro="Account verification isn't available yet."
    gapTitle="account verification"
    gap="No verification endpoint exists in the auth service. Add send-verification and confirm-verification routes and this screen can accept a code."
  />
);

export const MfaPage = () => (
  <FeatureGap
    title="Two-step verification"
    intro="MFA enrolment and verification aren't available yet."
    gapTitle="multi-factor authentication"
    gap="The auth service does not expose MFA enrol/verify routes today, and login has no challenge step. Once they exist, the login flow needs a second screen for the code."
  />
);
