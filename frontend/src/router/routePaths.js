/**
 * Centralized route path constants — avoids scattering magic
 * strings like "/inbox" or `/inbox/${id}` across components. Import
 * these anywhere a navigate() call or <Link> needs a path.
 *
 * Usage:
 *   import { ROUTES } from "@/router/routePaths";
 *   navigate(ROUTES.emailDetail(email.id));
 */
export const ROUTES = {
  login: "/login",
  dashboard: "/dashboard",
  inbox: "/inbox",
  emailDetail: (emailId) => `/inbox/${emailId}`,
  replyCenter: "/reply-center",
  copilot: "/copilot",
  tasks: "/tasks",
  meetings: "/meetings",
  meetingDetail: (meetingId) => `/meetings/${meetingId}`,
  analytics: "/analytics",
  automation: "/automation",
  settings: "/settings",
};