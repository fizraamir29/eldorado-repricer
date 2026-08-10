import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const token = typeof window !== "undefined" && localStorage.getItem("token");
    router.replace(token ? "/listings" : "/login");
  }, []);
  return null;
}
