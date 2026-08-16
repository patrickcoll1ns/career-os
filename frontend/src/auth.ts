import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
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
