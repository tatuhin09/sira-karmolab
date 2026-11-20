"""Evidence-linked practice feedback. Local hints require trainer confirmation."""
import hashlib
import json
import re
from core.research_contracts import ResearchRequest, ProviderExecutionResult

POLICY = [
 {"id":"1","bn":"অর্ডার নম্বর ও ক্ষতির ছবি সংগ্রহ করুন। দেওয়া তথ্য আবার চাইতে হবে না।","en":"Collect the order number and a damage photo. Do not request information already provided."},
 {"id":"2","bn":"নথি যাচাইয়ের জন্য পাঠান। সিদ্ধান্ত হলে ক্রেতাকে জানান।","en":"Send documents for verification and communicate the decision."},
 {"id":"3","bn":"যাচাই ও অনুমোদনের আগে টাকা ফেরত বা তার সময় নিশ্চিত করবেন না।","en":"Do not promise a refund or its timing before verification and approval."}
]
POLICY_VERSION = "sample-v1"
POLICY_HASH = hashlib.sha256(json.dumps(POLICY, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

CASES = {
 "initial": {
  "message":{"bn":"আজ মগটা হাতে পেয়েছি। প্যাকেট খুলে দেখি হাতলটা ভাঙা। টাকা ফেরত পেতে কী করতে হবে?",
             "en":"My mug arrived today with a broken handle. How can I get a refund?"},
  "provided":[],
 },
 "transfer": {
  "message":{"bn":"বাটিটার কিনারা ভাঙা এসেছে। অর্ডার নম্বর ৪৮২১ ও ক্ষতির ছবি দিয়েছি। এখন কী হবে?",
             "en":"The bowl arrived broken. My order number is 4821 and I have attached a damage photo. What happens next?"},
  "provided":["order","photo"],
 },
 "missing_photo": {
  "message":{"bn":"অর্ডার নম্বর ৫২৬৭। প্লেটটা ভাঙা এসেছে। ছবি এখনো পাঠাইনি। কী করতে হবে?",
             "en":"My order number is 5267. The plate arrived broken. I have not sent a photo yet. What should I do?"},
  "provided":["order"],
 },
 "timing": {
  "message":{"bn":"অর্ডার নম্বর ও ছবি আগেই দিয়েছি। যাচাই চলছে বলা হয়েছে। আপনি কি নিশ্চিত করতে পারেন আজই টাকা ফেরত পাব?",
             "en":"I already sent the order number and photo. Verification is in progress. Can you guarantee my refund today?"},
  "provided":["order","photo"],
 }
}
CUE_TEXT = {
 "promise":{"bn":"সময় নিশ্চিত করার মতো বাক্য পাওয়া গেছে। ধারা ৩ মেনে অনুমোদনের অবস্থা যাচাই করুন।",
            "en":"A possible timing commitment was found. Check approval under clause 3."},
 "repeat":{"bn":"ক্রেতার দেওয়া তথ্য আবার চাওয়ার সম্ভাবনা আছে। ধারা ১-এর সঙ্গে বাক্যটি মিলিয়ে দেখুন।",
           "en":"You may be requesting information already supplied. Review this sentence against clause 1."},
 "missing":{"bn":"প্রয়োজনীয় তথ্য চাওয়ার স্পষ্ট ইঙ্গিত পাওয়া যায়নি। প্রশিক্ষক প্রসঙ্গসহ যাচাই করবেন।",
            "en":"A clear request for missing information was not detected. A trainer will review the context."},
 "verification":{"bn":"যাচাইয়ের পর সিদ্ধান্ত জানানোর ভাষা শনাক্ত হয়েছে। পুরো উত্তর প্রশিক্ষক পর্যালোচনা করবেন।",
                 "en":"Verification language was detected. A trainer will review the complete response."}
}
ORDER = re.compile(r"অর্ডার|order", re.I)
PHOTO = re.compile(r"ছবি|ফটো|photo|image|picture", re.I)
REQUEST = re.compile(r"পাঠা|পাঠি|দিন|দেবেন|চাই|send|share|provide|need", re.I)
TIMING = re.compile(r"(?:আজই|আজকে|today).{0,55}(?:পাবেন|ফেরত|refund)|(?:refund|ফেরত).{0,55}(?:today|আজই|আজকে)", re.I)
VERIFY = re.compile(r"যাচাই|অনুমোদন|verif|approv", re.I)

def assess(answer, case_id):
    request = ResearchRequest(answer, "practice_review", max_results=3)
    if case_id not in CASES or len(answer) > 1500:
        raise ValueError("invalid assessment")
    findings = []
    provided = CASES[case_id]["provided"]
    sentences = [s.strip() for s in re.split(r"[।.!?\n]+", answer) if s.strip()]
    for sentence in sentences[:24]:
        if TIMING.search(sentence):
            findings.append({"kind":"promise","quote":sentence,"clause":"3"})
        if REQUEST.search(sentence) and any(
            name in provided and pattern.search(sentence)
            for name, pattern in [("order", ORDER), ("photo", PHOTO)]
        ):
            findings.append({"kind":"repeat","quote":sentence,"clause":"1"})
    for name, pattern in [("order",ORDER),("photo",PHOTO)]:
        if name not in provided and not any(pattern.search(s) and REQUEST.search(s) for s in sentences):
            findings.append({"kind":"missing","quote":"","clause":"1"})
            break
    if VERIFY.search(answer):
        findings.append({"kind":"verification","quote":next(s for s in sentences if VERIFY.search(s)),"clause":"2"})
    for finding in findings:
        finding["explanation"] = CUE_TEXT[finding["kind"]]
        finding["policy"] = next(p for p in POLICY if p["id"]==finding["clause"])
    kinds = {f["kind"] for f in findings}
    next_case = "transfer"
    if "promise" in kinds:
        next_case = "timing"
    elif "missing" in kinds:
        next_case = "missing_photo"
    result = ProviderExecutionResult(
        status="completed", provider_id="karmolab.local_cues",
        capability=request.capability, records=tuple(findings[:8]),
        resource_usage={"api_requests":0},
    )
    return {
        "status":"trainer_review_required", "engine":"local_cues",
        "policy_version":POLICY_VERSION,"policy_hash":POLICY_HASH,
        "findings":list(result.records), "case_message":CASES[case_id]["message"], "next_case":next_case,
        "next_message":CASES[next_case]["message"],
        "recommendation_reason": {
            "bn":"আপনার উত্তরে পাওয়া ইঙ্গিত অনুযায়ী পরের কেস বাছা হয়েছে। চূড়ান্ত মূল্যায়ন প্রশিক্ষকের।",
            "en":"The next case follows cues in your response. The trainer makes the final assessment."
        }
    }
