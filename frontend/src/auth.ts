import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

/**
 * Optional allowlist. An empty value lets any Google account sign in, which is
 * the right default for a public portfolio deployment; setting it restricts the
 * app — and the Anthropic spend behind it — to named accounts.
 */
const allowedEmails = new Set(
  (process.env.AUTH_ALLOWED_EMAILS ?? "")
    .split(",")
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean),
);

function isAllowed(email: unknown, emailVerified: unknown): boolean {
  if (typeof email !== "string" || emailVerified !== true) {
    return false;
  }
  return allowedEmails.size === 0 || allowedEmails.has(email.toLowerCase());
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  pages: { signIn: "/signin" },
  callbacks: {
    signIn({ profile }) {
      // Google is the only provider, so an unverified address is never trusted.
      return isAllowed(profile?.email, profile?.email_verified);
    },
    jwt({ token, account }) {
      if (account) {
        token.ownerId = `${account.provider}:${account.providerAccountId}`;
      }
      return token;
    },
    session({ session, token }) {
      if (typeof token.ownerId === "string") {
        session.user.ownerId = token.ownerId;
      }
      return session;
    },
    authorized({ auth, request }) {
      const publicPath = request.nextUrl.pathname === "/signin";
      return publicPath || Boolean(auth?.user?.ownerId);
    },
  },
});
