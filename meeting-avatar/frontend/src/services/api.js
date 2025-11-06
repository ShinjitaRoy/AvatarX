import axios from "axios";

const api = axios.create({
  baseURL: "/api",  // This will be proxied to Flask backend in dev
  timeout: 15000,
  headers: {
    "Content-Type": "application/json"
  }
});

export default api;