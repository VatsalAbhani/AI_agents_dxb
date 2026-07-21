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
      variants: [
        "Connecting you with our senior consultant now — they handle Marina purchases personally. Anything you'd like them to prepare?",
        "You clearly know what you want, Rahul — our senior consultant will reach out right away. Anything specific you'd like ready for that call?",
      ],
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
      variants: [
        "We have consultation slots tomorrow 2–6pm — shall I hold one for you?",
        "Hi Sara — lovely to hear from you! We'd be delighted to see you tomorrow; slots are open between 2 and 6pm. Want me to reserve the time that suits you best?",
      ],
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
      variants: [
        "The developer just released a new JVC payment schedule — want a quick call to go through it?",
        "Lovely to hear from you again, Omar! The new JVC payment schedule is out — shall we set up a quick call to walk through the options together?",
      ],
    },
  ];
  const rows = samples.map((s) => insertDraft(s));
  return NextResponse.json({ seeded: rows.length });
}
