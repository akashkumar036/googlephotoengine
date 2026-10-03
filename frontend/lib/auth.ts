import { AuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const authOptions: AuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Photo Discovery Engine",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "admin@example.com" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const res = await axios.post(`${API_BASE_URL}/auth/login`, {
            email: credentials.email,
            password: credentials.password,
          });

          const data = res.data;
          if (data.access_token) {
            // Fetch user info with access token
            const meRes = await axios.get(`${API_BASE_URL}/auth/me`, {
              headers: { Authorization: `Bearer ${data.access_token}` },
            });

            return {
              id: meRes.data.id,
              email: meRes.data.email,
              name: meRes.data.email.split("@")[0],
              role: meRes.data.role,
              accessToken: data.access_token,
              refreshToken: data.refresh_token,
            };
          }
          return null;
        } catch (error) {
          console.error("Auth authorization failed:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as unknown as { role?: string }).role;
        token.accessToken = (user as unknown as { accessToken?: string }).accessToken;
        token.refreshToken = (user as unknown as { refreshToken?: string }).refreshToken;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as unknown as { id?: string }).id = token.id as string;
        (session.user as unknown as { role?: string }).role = token.role as string;
        (session as unknown as { accessToken?: string }).accessToken = token.accessToken as string;
        (session as unknown as { refreshToken?: string }).refreshToken = token.refreshToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET || "dev-nextauth-secret-change-in-production-12345",
};
