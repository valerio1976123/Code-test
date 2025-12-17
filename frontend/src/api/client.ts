import axios from "axios";
import { toast } from "sonner";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  withCredentials: true,
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    const message =
      err?.response?.data?.message ??
      err?.response?.data?.error ??
      err?.message ??
      "Request failed";

    // Let auth flows handle 401 silently.
    if (status !== 401) {
      toast.error(message);
    }

    return Promise.reject(err);
  },
);

