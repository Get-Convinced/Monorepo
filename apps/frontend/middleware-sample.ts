// Rename this file to middleware.ts to wrap the entire application
// and enable automatic redirection to the login page or main app.
import { NextRequest, NextResponse } from "next/server";
import { handleSessionOnEdge } from "@frontegg/nextjs/edge";

const STATIC_EXTENSION = [
  "jpg",
  "jpeg",
  "png",
  "gif",
  "svg",
  "css",
  "ico",
  "webp",
];
const STATIC_PATTERN = new RegExp(`\\.(${STATIC_EXTENSION.join("|")})$`, "i");

export const middleware = async (request: NextRequest) => {
  const { pathname, searchParams } = request.nextUrl;
  const headers = request.headers;
  const isStaticResource = STATIC_PATTERN.test(pathname);

  // Skip middleware for static files like images
  if (isStaticResource) {
    return NextResponse.next();
  }

  return handleSessionOnEdge({ request, pathname, searchParams, headers });
};

export const config = {
  matcher: "/(.*)",
};
