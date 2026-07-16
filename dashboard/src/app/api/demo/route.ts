import { NextResponse } from "next/server";
import { insertDraft } from "@/lib/db";

// Seeds sample pending drafts — for sales demos and local testing only.
export async function POST() {
  const samples = [
    {
      lead_name: "Rahul M.",
      lead_meta: { source: "Meta Ads", enquiry: "2BR in Dubai Marina, ~2.4M, cash, this month" },
      channel: "whatsapp",
      draft:
        "You clearly know what you're looking for — connecting you with our senior consultant, who handles these personally. Anything you'd like them to prepare?",
      policy: ["HUMAN APPROVAL REQUIRED"],
      intent: { tier: "Hot", action: "escalate", high_intent: true },
      relationship: "new",
    },
    {
      lead_name: "Sara K.",
      lead_meta: { source: "Website form", enquiry: "Consultation availability" },
      channel: "whatsapp",
      draft:
        "Hi Sara — happy to help. We have consultation slots tomorrow between 2–6pm. Would you like me to hold one for you?",
      policy: ["HUMAN APPROVAL REQUIRED"],
      intent: { tier: "Warm", action: "ask", high_intent: false },
      relationship: "new",
    },
    {
      lead_name: "Omar A.",
      lead_meta: { source: "WhatsApp", enquiry: "Past buyer — asking about new payment plans" },
      channel: "whatsapp",
      draft:
        "Great to hear from you again, Omar. The developer has released a new schedule for JVC — shall I walk you through it over a quick call?",
      policy: ["HUMAN APPROVAL REQUIRED"],
      intent: { tier: "Warm", action: "share_options", high_intent: false },
      relationship: "returning",
    },
  ];
  const rows = samples.map((s) => insertDraft(s));
  return NextResponse.json({ seeded: rows.length });
}
