import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface User {
    ownerId: string;
  }

  interface Session {
    user: User;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    ownerId?: string;
  }
}
