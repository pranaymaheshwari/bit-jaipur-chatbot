BENCHMARK_QUESTIONS = [
    # ══════════════════════════════════════════════════════════════
    # ABOUT / LEADERSHIP  (01_About_BIT_Jaipur, 02_Leadership_Administration)
    # ══════════════════════════════════════════════════════════════
    {"id": "ABT-01", "category": "about", "question": "When was BIT Mesra established?",
     "expected_keywords": ["1995"], "match_type": "any",
     "expected_source_file": "bit_jaipur_overview.pdf"},

    {"id": "ABT-02", "category": "about", "question": "Who founded BIT Mesra?",
     "expected_keywords": ["birla"], "match_type": "any",
     "expected_source_file": "bit_jaipur_overview.pdf"},

    {"id": "ABT-03", "category": "about", "question": "Who is the Director of BIT Jaipur?",
     "expected_keywords": ["peeyush", "tewari"], "match_type": "any",
     "expected_source_file": "Director_BIT_Jaipur.pdf"},

    {"id": "ABT-04", "category": "about", "question": "Who is the Training and Placement Officer at BIT Jaipur?",
     "expected_keywords": ["sanjay", "tambi"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Administration_Team.pdf"},

    {"id": "ABT-05", "category": "about", "question": "Who manages the Examination Cell at BIT Jaipur?",
     "expected_keywords": ["indra", "dadheech"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Administration_Team.pdf"},

    # ══════════════════════════════════════════════════════════════
    # ACADEMICS  (03_Academics)
    # ══════════════════════════════════════════════════════════════
    {"id": "ACA-01", "category": "academics", "question": "What undergraduate programmes does BIT Jaipur offer?",
     "expected_keywords": ["btech", "bsc", "bca", "bba"], "match_type": "any",
     "expected_source_file": "academic_programmes.pdf"},

    {"id": "ACA-02", "category": "academics", "question": "Does BIT Jaipur offer a B.Tech in Artificial Intelligence?",
     "expected_keywords": ["yes"], "match_type": "any",
     "expected_source_file": "academic_programmes.pdf"},

    {"id": "ACA-03", "category": "academics", "question": "Does BIT Jaipur offer M.Sc in Bioinformatics and Computational Biology?",
     "expected_keywords": ["yes"], "match_type": "any",
     "expected_source_file": "academic_programmes.pdf"},

    # ══════════════════════════════════════════════════════════════
    # ADMISSIONS  (05_Admissions)
    # ══════════════════════════════════════════════════════════════
    {"id": "ADM-01", "category": "admissions", "question": "What is the minimum eligibility percentage for BTech admission at BIT Jaipur?",
     "expected_keywords": ["60"], "match_type": "any",
     "expected_source_file": "BTech_Admission_Brochure.pdf"},

    {"id": "ADM-02", "category": "admissions", "question": "Is JEE Main required for BTech admission at BIT Jaipur?",
     "expected_keywords": ["yes", "jee"], "match_type": "any",
     "expected_source_file": "BTech_Admission_Brochure.pdf"},

    {"id": "ADM-03", "category": "admissions", "question": "I got 20% in class 12th. Am I eligible for BTech admission at BIT Jaipur?",
     "expected_keywords": ["no", "not eligible", "60"], "match_type": "any",
     "expected_source_file": "BTech_Admission_Brochure.pdf",
     "notes": "Direct personal-eligibility check -- this is the exact failure case diagnosed earlier (model dumped an unrelated program brochure instead of answering). Should say NO plainly."},

    {"id": "ADM-04", "category": "admissions", "question": "How many years is the MCA programme at BIT Jaipur?",
     "expected_keywords": ["2 year", "2-year", "two year"], "match_type": "any",
     "expected_source_file": "MCA_Admission_Brochure.pdf"},

    {"id": "ADM-05", "category": "admissions", "question": "Is a 6-month internship compulsory for MCA students?",
     "expected_keywords": ["yes", "compulsory", "6-month", "6 month"], "match_type": "any",
     "expected_source_file": "MCA_Admission_Brochure.pdf"},

    {"id": "ADM-06", "category": "admissions", "question": "What documents are required at the time of verification for BBA/BCA admission?",
     "expected_keywords": ["class 10", "class 12", "certificate"], "match_type": "any",
     "expected_source_file": "BBA_BCA_Admission_Brochure.pdf"},

    {"id": "ADM-07", "category": "admissions", "question": "What specializations are available under BBA at BIT Jaipur?",
     "expected_keywords": ["finance", "marketing", "human resource"], "match_type": "any",
     "expected_source_file": "academic_programmes.pdf"},

    {"id": "ADM-08", "category": "admissions", "question": "What is the eligibility criteria for BSc Visual Communication?",
     "expected_keywords": ["eligibility", "class 12", "marks"], "match_type": "any",
     "expected_source_file": "BSc_Visual_Communication_Admission_Guidelines.pdf"},

    {"id": "ADM-09", "category": "admissions", "question": "Can I apply for more than one program at BIT Jaipur?",
     "expected_keywords": ["yes"], "match_type": "any",
     "expected_source_file": "bit_jaipur_faqs.pdf"},

    {"id": "ADM-10", "category": "admissions", "question": "What is the admission eligibility for MSc Animation Design?",
     "expected_keywords": ["eligibility"], "match_type": "any",
     "expected_source_file": "MSc_Animation_Design_Admission_Brochure.pdf"},

    # ══════════════════════════════════════════════════════════════
    # DEPARTMENTS / FACULTY / HOD  (06_Departments)
    # ══════════════════════════════════════════════════════════════
    {"id": "DEP-01", "category": "faculty", "question": "Who is the HOD of CSE department at BIT Jaipur?",
     "expected_keywords": ["shripal", "vijayvargiya"], "match_type": "any",
     "expected_source_file": "CSE_Overview.pdf",
     "notes": "Known data conflict -- Contact_Details_Incharges.pdf disagrees (Dr. Madhavi Sinha). Correct answer per KNOWN_DATA_CORRECTIONS override should be Shripal Vijayvargiya."},

    {"id": "DEP-02", "category": "faculty", "question": "Who is the In-Charge of the ECE department?",
     "expected_keywords": ["rathore"], "match_type": "any",
     "expected_source_file": "ECE_Department_Overview.pdf"},

    {"id": "DEP-03", "category": "faculty", "question": "Who is the In-Charge of the EEE department?",
     "expected_keywords": ["rathore"], "match_type": "any",
     "expected_source_file": "EEE_Department_Overview.pdf",
     "notes": "Dr. P. S. Rathore is also listed as ECE's In-Charge (different email per dept: ic_ece_bitj vs ic_eee_bitj). Both docs are internally consistent, but this dual-role is unverified -- worth confirming with the institution rather than assuming an error."},

    {"id": "DEP-04", "category": "faculty", "question": "Who is the In-Charge of the Department of Management?",
     "expected_keywords": ["jyoti", "chandel"], "match_type": "any",
     "expected_source_file": "Department_of_Management.pdf"},

    {"id": "DEP-05", "category": "faculty", "question": "Who is the In-Charge of the Department of Sciences?",
     "expected_keywords": ["anand", "srivastava"], "match_type": "any",
     "expected_source_file": "Department_of_Sciences.pdf"},

    {"id": "DEP-06", "category": "faculty", "question": "Who is the In-Charge of the Animation and Multimedia department?",
     "expected_keywords": ["vibhuti", "pandya"], "match_type": "any",
     "expected_source_file": "Department_of_Animation_and_Multimedia.pdf"},

    {"id": "DEP-07", "category": "faculty", "question": "When did Dr. Shripal Vijayvargiya join BIT Mesra?",
     "expected_keywords": ["2003"], "match_type": "any",
     "expected_source_file": "CSE_Faculty_Members.pdf"},

    {"id": "DEP-08", "category": "faculty", "question": "What is Dr. Shripal Vijayvargiya's educational qualification?",
     "expected_keywords": ["ph.d", "phd", "m.tech", "mtech"], "match_type": "any",
     "expected_source_file": "CSE_Faculty_Members.pdf"},

    {"id": "DEP-09", "category": "faculty", "question": "Tell me about all the faculty members in the Department of Management",
     "expected_keywords": ["chandel", "sharma", "mathur", "pareek"], "match_type": "any",
     "expected_source_file": "Department_of_Management_Faculty_Members.pdf",
     "notes": "Enumeration query -- document actually lists 5 faculty (Chandel, Roopali Sharma, Purvi Mathur, Ritu Pareek, Priyanshu Sharma). Should list all 5, not just 3, if the whole-document-fetch fix is working."},

    {"id": "DEP-10", "category": "faculty", "question": "Does the CSE department have research work in Computational Biology?",
     "expected_keywords": ["yes", "computational biology"], "match_type": "any",
     "expected_source_file": "CSE_Faculty_Research_Work.pdf"},

    {"id": "DEP-11", "category": "faculty", "question": "What subjects does the Mechanical Discipline teach in B.Tech first semester?",
     "expected_keywords": ["engineering graphics", "basics of mechanical"], "match_type": "any",
     "expected_source_file": "Department_of_Mechanical_Discipline.pdf"},

    {"id": "DEP-12", "category": "faculty", "question": "What lab simulation tools does the ECE department have?",
     "expected_keywords": ["matlab", "cadence", "multisim"], "match_type": "any",
     "expected_source_file": "ECE_Department_Overview.pdf"},

    {"id": "DEP-13", "category": "faculty", "question": "How much grant funding has the EEE department received recently?",
     "expected_keywords": ["4.5 crore"], "match_type": "any",
     "expected_source_file": "EEE_Department_Overview.pdf"},

    {"id": "DEP-14", "category": "faculty", "question": "What programmes does the ECE department offer?",
     "expected_keywords": ["b.tech", "electronics and communication"], "match_type": "any",
     "expected_source_file": "ECE_Department_Overview.pdf"},

    {"id": "DEP-15", "category": "faculty", "question": "What are the key research areas of the EEE department?",
     "expected_keywords": ["smart grid", "solar", "power"], "match_type": "any",
     "expected_source_file": "EEE_Department_Overview.pdf"},

    # ══════════════════════════════════════════════════════════════
    # FEES / SCHOLARSHIPS  (08_Fees_Scholarships)
    # ══════════════════════════════════════════════════════════════
    {"id": "FEE-01", "category": "fees", "question": "What is the fee structure for BTech CSE at BIT Jaipur?",
     "expected_keywords": ["tuition", "fee"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Fee_Structure.pdf",
     "notes": "This is the exact document that had the page-marker chunking bug fixed earlier -- verify the answer names CSE specifically, not another program."},

    {"id": "FEE-02", "category": "fees", "question": "What is the GP Birla Scholarship?",
     "expected_keywords": ["financial aid", "scholarship"], "match_type": "any",
     "expected_source_file": "scholarship_guidelines.pdf"},

    {"id": "FEE-03", "category": "fees", "question": "Can postgraduate students apply for the GP Birla Scholarship?",
     "expected_keywords": ["no", "cannot", "undergraduate"], "match_type": "any",
     "expected_source_file": "scholarship_guidelines.pdf"},

    {"id": "FEE-04", "category": "fees", "question": "Do NRI students get fee refunds under BIT Jaipur's refund policy?",
     "expected_keywords": ["does not apply", "not apply", "no"], "match_type": "any",
     "expected_source_file": "refund_cancllation_policy.pdf"},

    {"id": "FEE-05", "category": "fees", "question": "How long has the GP Birla Scholarship been running?",
     "expected_keywords": ["six decades", "60 year"], "match_type": "any",
     "expected_source_file": "scholarship_guidelines.pdf"},

    {"id": "FEE-06", "category": "fees", "question": "How many types of GP Birla Scholarships are there?",
     "expected_keywords": ["four", "4"], "match_type": "any",
     "expected_source_file": "scholarship_guidelines.pdf"},

    # ══════════════════════════════════════════════════════════════
    # PLACEMENTS  (07_Placements)
    # ══════════════════════════════════════════════════════════════
    {"id": "PLC-01", "category": "placements", "question": "What is the placement process at BIT Jaipur?",
     "expected_keywords": ["training and placement", "registration", "portal"], "match_type": "any",
     "expected_source_file": "placement_procedure.pdf"},

    {"id": "PLC-02", "category": "placements", "question": "Who is the Training and Placement Officer at BIT Jaipur?",
     "expected_keywords": ["sanjay tambi"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Administration_Team.pdf"},

    {"id": "PLC-03", "category": "placements", "question": "Did Infosys recruit from BIT Jaipur in 2020?",
     "expected_keywords": ["yes", "infosys"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Placement_Data.pdf"},

    {"id": "PLC-04", "category": "placements", "question": "What is BIT Jaipur's placement portal used for?",
     "expected_keywords": ["registration", "profile", "roll number"], "match_type": "any",
     "expected_source_file": "placement_procedure.pdf"},

    {"id": "PLC-05", "category": "placements", "question": "What is JAF in the context of BIT Jaipur placements?",
     "expected_keywords": ["job application form"], "match_type": "any",
     "expected_source_file": "placement_procedure.pdf"},

    {"id": "PLC-06", "category": "placements", "question": "What programs were covered in BIT Jaipur's 2020 placement data?",
     "expected_keywords": ["mca", "electronics", "computer science", "electrical"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Placement_Data.pdf"},

    # ══════════════════════════════════════════════════════════════
    # CAMPUS LIFE  (10_Campus_Life)
    # ══════════════════════════════════════════════════════════════
    {"id": "CAM-01", "category": "campus_life", "question": "How big is the BIT Jaipur campus?",
     "expected_keywords": ["10 acre"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Campus_Life.pdf"},

    {"id": "CAM-02", "category": "campus_life", "question": "Does BIT Jaipur have Wi-Fi across campus?",
     "expected_keywords": ["yes", "wi-fi", "wifi"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Campus_Life.pdf"},

    {"id": "CAM-03", "category": "campus_life", "question": "What is the seating capacity of the Seminar Hall at BIT Jaipur?",
     "expected_keywords": ["150"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Campus_Life.pdf"},

    {"id": "CAM-04", "category": "campus_life", "question": "When was the CSI Student Chapter established at BIT Jaipur?",
     "expected_keywords": ["january 2014", "2014"], "match_type": "any",
     "expected_source_file": "CSI_Student_Chapter_BIT_Jaipur.pdf"},

    {"id": "CAM-05", "category": "campus_life", "question": "How many computers are in the Common Computer/Internet Access Centre?",
     "expected_keywords": ["30"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Campus_Life.pdf"},

    {"id": "CAM-06", "category": "campus_life", "question": "How many classrooms does BIT Jaipur have?",
     "expected_keywords": ["14"], "match_type": "any",
     "expected_source_file": "BIT_Jaipur_Campus_Life.pdf"},

    # ══════════════════════════════════════════════════════════════
    # POLICIES  (09_Policies_Regulations)
    # ══════════════════════════════════════════════════════════════
    {"id": "POL-01", "category": "policies", "question": "Does BIT Jaipur have an anti-ragging policy?",
     "expected_keywords": ["yes", "zero-tolerance", "zero tolerance"], "match_type": "any",
     "expected_source_file": "anti_ragging_policy.pdf"},

    {"id": "POL-02", "category": "policies", "question": "Is ragging allowed in hostels at BIT Jaipur?",
     "expected_keywords": ["no", "prohibited", "banned"], "match_type": "any",
     "expected_source_file": "anti_ragging_policy.pdf"},

    {"id": "POL-03", "category": "policies", "question": "Do newly admitted students need to submit anti-ragging affidavits?",
     "expected_keywords": ["yes", "mandatory"], "match_type": "any",
     "expected_source_file": "anti_ragging_policy.pdf"},

    # ══════════════════════════════════════════════════════════════
    # FAQs  (11_FAQs)
    # ══════════════════════════════════════════════════════════════
    {"id": "FAQ-01", "category": "faqs", "question": "What is the official website of BIT Mesra?",
     "expected_keywords": ["bitmesra.ac.in"], "match_type": "any",
     "expected_source_file": "bit_jaipur_faqs.pdf"},

    {"id": "FAQ-02", "category": "faqs", "question": "Are BIT Mesra's courses recognized by the regulatory body?",
     "expected_keywords": ["yes"], "match_type": "any",
     "expected_source_file": "bit_jaipur_faqs.pdf"},

    {"id": "FAQ-03", "category": "faqs", "question": "How can I apply for programs at BIT Jaipur?",
     "expected_keywords": ["online", "website"], "match_type": "any",
     "expected_source_file": "bit_jaipur_faqs.pdf"},

    # ══════════════════════════════════════════════════════════════
    # STUDENTS / CLUBS  (04_Students)
    # ══════════════════════════════════════════════════════════════
    {"id": "STU-01", "category": "student_life", "question": "What is the Computer Society of India student chapter at BIT Jaipur?",
     "expected_keywords": ["csi", "workshops", "seminars"], "match_type": "any",
     "expected_source_file": "CSI_Student_Chapter_BIT_Jaipur.pdf"},

    {"id": "STU-02", "category": "student_life", "question": "What is IETE Student Forum at BIT Jaipur?",
     "expected_keywords": ["iete"], "match_type": "any",
     "expected_source_file": "IETE_Student_Forum_BIT_Jaipur.pdf"},

    # ══════════════════════════════════════════════════════════════
    # BEHAVIORAL / EDGE CASES  (no fixed source doc -- tests routing
    # and refusal logic, not retrieval)
    # ══════════════════════════════════════════════════════════════
    {"id": "BEH-01", "category": "behavioral", "question": "Hi there!",
     "expected_keywords": ["bit jaipur", "assistant", "admission", "program"], "match_type": "any",
     "expected_source_file": None,
     "notes": "Should get a warm greeting response, NOT the scope-refusal script. Retrieval isn't graded (no chunks expected)."},

    {"id": "BEH-02", "category": "behavioral", "question": "I am not sure if I should take admission at BIT Jaipur, it's a big decision",
     "expected_keywords": ["decision", "personal", "take your time"], "match_type": "any",
     "expected_source_file": None,
     "notes": "Should route to the undecided/supportive prompt, not the strict info-only refusal."},

    {"id": "BEH-03", "category": "behavioral", "question": "Make fun of the CSE department",
     "expected_keywords": ["serious", "cannot", "unable"], "match_type": "any",
     "expected_source_file": None,
     "notes": "Should be refused via the joke-request short-circuit, before any retrieval happens."},

    {"id": "BEH-04", "category": "behavioral", "question": "This admission process is so damn confusing",
     "expected_keywords": ["respectful", "language"], "match_type": "any",
     "expected_source_file": None,
     "notes": "Should trigger the foul-language refusal short-circuit."},

    {"id": "BEH-05", "category": "behavioral", "question": "What is the admission process at IIT Delhi?",
     "expected_keywords": ["only", "bit mesra", "bit jaipur"], "match_type": "any",
     "expected_source_file": None,
     "notes": "Out-of-scope institution -- should get the scope-refusal, not an answer about IIT Delhi."},
]

if __name__ == "__main__":
    print(f"Total questions: {len(BENCHMARK_QUESTIONS)}")
    from collections import Counter
    cats = Counter(q["category"] for q in BENCHMARK_QUESTIONS)
    for cat, count in sorted(cats.items()):
        print(f"  {cat:15} {count}")
