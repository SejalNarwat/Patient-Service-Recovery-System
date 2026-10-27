"""
Synthetic patient feedback dataset generator.
Creates 40 de-identified patient feedback records covering all major themes:
appointment delays, communication gaps, scheduling issues, and care experience.
"""

SYNTHETIC_FEEDBACK = [
    # --- Appointment Delay Cases ---
    {
        "feedback_id": "PF-2024-001",
        "submission_date": "2024-01-08",
        "department": "Cardiology",
        "feedback_text": (
            "I had an appointment scheduled for 10 AM but was not seen until 1:30 PM. "
            "No one informed me of the delay or gave an update. I missed work because of this "
            "and felt completely ignored by the front desk staff."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-002",
        "submission_date": "2024-01-10",
        "department": "Orthopaedics",
        "feedback_text": (
            "My follow-up appointment was postponed three times over six weeks. "
            "Each cancellation came less than 24 hours before the appointment. "
            "My recovery has been set back because I could not get the guidance I needed in time."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-003",
        "submission_date": "2024-01-12",
        "department": "General Medicine",
        "feedback_text": (
            "Waited over two hours in the waiting room with no explanation. "
            "The receptionist was unhelpful when I asked for an update. "
            "This is not the first time this has happened."
        ),
        "contact_method": "Verbal",
    },
    {
        "feedback_id": "PF-2024-004",
        "submission_date": "2024-01-15",
        "department": "Radiology",
        "feedback_text": (
            "My scan results took over three weeks to reach my GP. "
            "During this time I was very anxious and could not plan my next steps. "
            "There was no proactive communication from the radiology team."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-005",
        "submission_date": "2024-01-18",
        "department": "Oncology",
        "feedback_text": (
            "I am extremely concerned. My chemotherapy appointment was delayed by two weeks "
            "without any medical reason given. I was told it was an administrative error. "
            "This has caused me significant distress and I worry about my treatment plan."
        ),
        "contact_method": "Written",
    },
    # --- Communication Gap Cases ---
    {
        "feedback_id": "PF-2024-006",
        "submission_date": "2024-01-20",
        "department": "Neurology",
        "feedback_text": (
            "After my MRI, no one followed up to discuss the results. "
            "I called the department four times over two weeks and could not reach anyone. "
            "I only received information when my GP chased the hospital on my behalf."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-007",
        "submission_date": "2024-01-22",
        "department": "Diabetes Clinic",
        "feedback_text": (
            "The discharge instructions were unclear. I was not told when to take my new medication "
            "or whether it could interact with my existing prescription. I had to call the pharmacy "
            "to clarify, which caused unnecessary stress."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-008",
        "submission_date": "2024-01-25",
        "department": "Surgical Ward",
        "feedback_text": (
            "No one explained the post-surgery care plan to my family. "
            "We were unsure about wound care, diet restrictions, and when to return for a check-up. "
            "The nurse seemed rushed and we felt like a burden for asking questions."
        ),
        "contact_method": "Verbal",
    },
    {
        "feedback_id": "PF-2024-009",
        "submission_date": "2024-01-28",
        "department": "Paediatrics",
        "feedback_text": (
            "Letters about my child's appointment were sent to an old address despite us updating "
            "our contact details twice. We nearly missed the specialist appointment as a result. "
            "The administration team needs to improve how they manage patient records."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-010",
        "submission_date": "2024-02-01",
        "department": "Mental Health",
        "feedback_text": (
            "I was referred to the mental health team three months ago. "
            "I have not received any appointment confirmation or contact. "
            "I am struggling significantly and feel forgotten by the system."
        ),
        "contact_method": "Online",
    },
    # --- Scheduling Issues ---
    {
        "feedback_id": "PF-2024-011",
        "submission_date": "2024-02-03",
        "department": "Physiotherapy",
        "feedback_text": (
            "The online booking system kept showing errors and I could not confirm my appointment. "
            "When I called, I was placed on hold for 45 minutes. This is unacceptable for patients "
            "who work full-time and cannot easily access services."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-012",
        "submission_date": "2024-02-06",
        "department": "Cardiology",
        "feedback_text": (
            "My appointment was double-booked and I was told to wait another month. "
            "I have chest pains and the additional wait is causing me anxiety. "
            "The scheduler was apologetic but could not offer an earlier slot."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-013",
        "submission_date": "2024-02-08",
        "department": "Dermatology",
        "feedback_text": (
            "I received two conflicting appointment letters on the same day for the same condition. "
            "When I attended the first appointment, it had been cancelled in the system "
            "without anyone notifying me. I travelled 40 minutes for nothing."
        ),
        "contact_method": "Verbal",
    },
    {
        "feedback_id": "PF-2024-014",
        "submission_date": "2024-02-10",
        "department": "Ophthalmology",
        "feedback_text": (
            "The waiting time for an initial appointment was 14 weeks. "
            "For a vision-related issue, this seems excessively long. "
            "I would appreciate faster access pathways or at least interim guidance."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-015",
        "submission_date": "2024-02-12",
        "department": "General Medicine",
        "feedback_text": (
            "My appointment was automatically moved to a different site without asking me. "
            "The new location has no public transport links and I do not drive. "
            "Access issues are not being considered when making these decisions."
        ),
        "contact_method": "Online",
    },
    # --- Care Experience ---
    {
        "feedback_id": "PF-2024-016",
        "submission_date": "2024-02-14",
        "department": "Emergency Department",
        "feedback_text": (
            "The staff were kind and professional. Despite a long wait, I was kept informed "
            "and felt cared for throughout my visit. The nurse who treated me was exceptional."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-017",
        "submission_date": "2024-02-16",
        "department": "Maternity",
        "feedback_text": (
            "The midwife team was wonderful and very supportive during my delivery. "
            "However, the postnatal ward was understaffed and I struggled to get help with "
            "breastfeeding in the first 24 hours. I felt unsupported during a critical time."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-018",
        "submission_date": "2024-02-18",
        "department": "Orthopaedics",
        "feedback_text": (
            "The consultant spoke about me rather than to me during the consultation. "
            "I felt dismissed when I raised concerns about the proposed treatment. "
            "I would like to be treated as a partner in my own healthcare decisions."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-019",
        "submission_date": "2024-02-20",
        "department": "Renal Unit",
        "feedback_text": (
            "The dialysis chair was broken on two consecutive visits and I had to wait "
            "for a suitable station. Equipment maintenance seems to be a recurring problem. "
            "For dialysis patients, delays and discomfort have serious health implications."
        ),
        "contact_method": "Verbal",
    },
    {
        "feedback_id": "PF-2024-020",
        "submission_date": "2024-02-22",
        "department": "Outpatient Clinic",
        "feedback_text": (
            "The waiting area was too hot and overcrowded. There were not enough seats. "
            "Elderly patients were standing for over an hour. This is a dignity and safety issue."
        ),
        "contact_method": "Online",
    },
    # --- Medication / Safety-adjacent ---
    {
        "feedback_id": "PF-2024-021",
        "submission_date": "2024-02-25",
        "department": "Pharmacy",
        "feedback_text": (
            "I was given the wrong dosage instructions on my prescription label. "
            "I only noticed when I checked with my GP. This could have caused a serious problem. "
            "The pharmacist did not check with me before I left."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-022",
        "submission_date": "2024-02-27",
        "department": "Surgical Ward",
        "feedback_text": (
            "My allergy to penicillin was clearly documented but I was still prescribed amoxicillin "
            "upon discharge. I flagged this to the nurse who seemed surprised. "
            "This kind of error must not happen."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-023",
        "submission_date": "2024-03-01",
        "department": "Diabetes Clinic",
        "feedback_text": (
            "My insulin prescription was not renewed in time and I ran out for two days. "
            "Despite calling ahead, the repeat prescription was not actioned. "
            "This directly affected my blood sugar management."
        ),
        "contact_method": "Online",
    },
    # --- Repeated / Escalated Failures ---
    {
        "feedback_id": "PF-2024-024",
        "submission_date": "2024-03-03",
        "department": "Cardiology",
        "feedback_text": (
            "This is my fourth complaint about the same issue: no parking available near the clinic "
            "and no information provided about alternatives. I have raised this before with no response."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-025",
        "submission_date": "2024-03-05",
        "department": "General Medicine",
        "feedback_text": (
            "I have submitted two previous complaints about appointment cancellations. "
            "Nothing has changed. I am now formally requesting escalation to the patient experience manager."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-026",
        "submission_date": "2024-03-07",
        "department": "Outpatient Clinic",
        "feedback_text": (
            "The interpreter service I requested was not arranged for the third time. "
            "Without an interpreter, I cannot understand my diagnosis or treatment. "
            "This is affecting my health outcomes and is a matter of equity and safety."
        ),
        "contact_method": "Verbal",
    },
    # --- Positive / Mixed ---
    {
        "feedback_id": "PF-2024-027",
        "submission_date": "2024-03-09",
        "department": "Oncology",
        "feedback_text": (
            "My oncologist and the specialist nurse have been outstanding. "
            "They are always thorough, compassionate, and available to answer questions. "
            "I feel genuinely supported through a very difficult experience."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-028",
        "submission_date": "2024-03-11",
        "department": "Physiotherapy",
        "feedback_text": (
            "The physiotherapy sessions have been very helpful and my mobility has improved greatly. "
            "My only suggestion is that the waiting room could do with better seating for people "
            "who have mobility difficulties."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-029",
        "submission_date": "2024-03-12",
        "department": "Cardiology",
        "feedback_text": (
            "Overall experience was positive. The consultant was thorough and explained everything clearly. "
            "The only issue was that the appointment was 30 minutes late with no explanation."
        ),
        "contact_method": "Online",
    },
    # --- Ambiguous / Needs Clarification ---
    {
        "feedback_id": "PF-2024-030",
        "submission_date": "2024-03-14",
        "department": "General Medicine",
        "feedback_text": (
            "Something did not feel right during my visit last week. "
            "I am not sure how to describe it but I left feeling unsettled. "
            "I hope someone follows up with me."
        ),
        "contact_method": "Verbal",
    },
    {
        "feedback_id": "PF-2024-031",
        "submission_date": "2024-03-15",
        "department": "Surgical Ward",
        "feedback_text": (
            "I am not satisfied."
        ),
        "contact_method": "Online",
    },
    # --- Mental Health / Dignity ---
    {
        "feedback_id": "PF-2024-032",
        "submission_date": "2024-03-17",
        "department": "Mental Health",
        "feedback_text": (
            "I was told my crisis support referral would be processed within 48 hours. "
            "It has now been three weeks and I have heard nothing. "
            "I am in a very difficult place right now and this delay is harmful."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-033",
        "submission_date": "2024-03-19",
        "department": "Mental Health",
        "feedback_text": (
            "The inpatient team treated me with respect and the therapeutic environment was good. "
            "My concern is about the transition back to community support — "
            "it felt abrupt and I did not have enough information about ongoing resources."
        ),
        "contact_method": "Written",
    },
    # --- Access and Equality ---
    {
        "feedback_id": "PF-2024-034",
        "submission_date": "2024-03-20",
        "department": "Outpatient Clinic",
        "feedback_text": (
            "The patient portal is not accessible on older mobile devices. "
            "Not everyone has a laptop. Many elderly and low-income patients cannot "
            "access appointment information or test results digitally."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-035",
        "submission_date": "2024-03-22",
        "department": "Renal Unit",
        "feedback_text": (
            "Transport assistance was cancelled without notice. "
            "As a dialysis patient I cannot miss sessions. "
            "I need reliable transport support to attend my life-sustaining treatment."
        ),
        "contact_method": "Verbal",
    },
    # --- Additional Variety ---
    {
        "feedback_id": "PF-2024-036",
        "submission_date": "2024-03-24",
        "department": "Radiology",
        "feedback_text": (
            "The radiographer was professional and the procedure was explained clearly. "
            "The facility was clean and modern. No complaints — a genuinely good experience."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-037",
        "submission_date": "2024-03-26",
        "department": "Paediatrics",
        "feedback_text": (
            "The paediatric ward staff were wonderful with my daughter. "
            "They made a scary experience manageable. "
            "The play specialist in particular deserves special recognition."
        ),
        "contact_method": "Online",
    },
    {
        "feedback_id": "PF-2024-038",
        "submission_date": "2024-03-27",
        "department": "Emergency Department",
        "feedback_text": (
            "I waited 6 hours with severe abdominal pain. I was triaged as low priority but "
            "it turned out I had appendicitis. I question whether triage assessments are "
            "consistently accurate, especially during busy periods."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-039",
        "submission_date": "2024-03-28",
        "department": "Ophthalmology",
        "feedback_text": (
            "My vision has deteriorated noticeably since my last visit six months ago. "
            "I have called to bring forward my appointment but have been told there are no slots. "
            "I feel my condition is not being taken seriously given the rate of change."
        ),
        "contact_method": "Written",
    },
    {
        "feedback_id": "PF-2024-040",
        "submission_date": "",  # missing field to test data quality agent
        "department": "General Medicine",
        "feedback_text": (
            "Not happy with my experience. The whole process needs to be reviewed."
        ),
        "contact_method": "",  # missing field
    },
]
