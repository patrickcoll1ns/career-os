import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [GitHub],
  pages: { signIn: "/signin" },
  callbacks: {
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
