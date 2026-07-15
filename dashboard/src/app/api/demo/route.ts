import { NextResponse } from "next/server";
import { insertDraft } from "@/lib/db";

// Seeds sample pending drafts — for sales demos and local testing only.
export async function POST() {
  const samples = [
    {
      lead_name: "Rahul M.",
      lead_meta: { source: "Meta Ads", enquiry: "2BR in Dubai Marina, ~2.4M" },
      channel: "whatsapp",
      draft:
        "Marina Vista fits — 2BR in Dubai Marina, AED 2.3M, ready. Shall I set up a viewing this week?",
      policy: ["HUMAN APPROVAL REQUIRED"],
    },
    {
      lead_name: "Sara K.",
      lead_meta: { source: "Website form", enquiry: "Consultation availability" },
      channel: "whatsapp",
      draft:
        "Hi Sara — happy to help. We have consultation slots tomorrow between 2–6pm. Would you like me to hold one for you?",
      policy: ["HUMAN APPROVAL REQUIRED"],
    },
    {
      lead_name: "Omar A.",
      lead_meta: { source: "WhatsApp", enquiry: "Asking about payment plans" },
      channel: "whatsapp",
      draft:
        "We can discuss flexible payment plan options for the JVC unit — I can share the developer's official schedule. When suits a quick call?",
      policy: ["HUMAN APPROVAL REQUIRED", "PAYMENT TERMS MENTIONED"],
    },
  ];
  const rows = samples.map((s) => insertDraft(s));
  return NextResponse.json({ seeded: rows.length });
}
