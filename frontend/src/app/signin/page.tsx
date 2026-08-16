import { signIn } from "@/auth";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f4f7f5] px-6">
      <section className="w-full max-w-md rounded-3xl border border-[#dce6df] bg-white p-10 text-center shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#52705f]">
          CareerOS
        </p>
        <h1 className="mt-4 text-3xl font-semibold text-[#203329]">
          Your career workspace
        </h1>
        <p className="mt-3 text-sm leading-6 text-[#5c6f64]">
          Sign in to keep your goals, documents, coaching, and interview history
          private to your account.
        </p>
        <form
          className="mt-8"
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/" });
          }}
        >
          <button
            className="w-full rounded-xl bg-[#203329] px-5 py-3 font-semibold text-white transition hover:bg-[#314d3d]"
            type="submit"
          >
            Continue with Google
          </button>
        </form>
      </section>
    </main>
  );
}
