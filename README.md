# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
**Domain:** Student experiences with Professor Alexa (Alex) Doboli's courses (ESE 124, 224, 344) at Stony Brook University.

This knowledge is valuable to students deciding whether to take Professor Doboli or how to prepare for his courses, but it is scattered and hard to find through official channels. The university only publishes a faculty bio and aggregate course-evaluation numbers — it doesn't surface the actual qualitative experience: what the lectures are like, how the labs and final project really go, how the AI/self-learning teaching style lands, and how the courses compare to each other. That candid information lives across Rate My Professors, official course-evaluation comments, and several scattered Reddit threads. A RAG system consolidates these perspectives into one place so a student can ask a direct question and get an answer grounded in real reviews.
---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors | 35 student ratings of Prof. Doboli with quality/difficulty scores and written reviews across his courses | documents/dobolirmp_cleaned.txt |
| 2 | SBU Official Course Evaluation — ESE 124 | Student evaluation comments on the intro C programming course (what was valuable / what could improve) | documents/doboliese124_cleaned.txt |
| 3 | SBU Official Course Evaluation — ESE 224 | Student evaluation comments on the C++/data-structures course | documents/doboliese224_cleaned.txt |
| 4 | SBU Official Course Evaluation — ESE 344 | Student evaluation comments on the data structures & algorithms course | documents/doboliese344_cleaned.txt |
| 5 | Reddit r/SBU — single-student review | One student's reviews of all three Doboli courses (ESE 124/224/344) with ratings | documents/doboliclasses_cleaned.txt |
| 6 | Reddit r/SBU — teacher rating thread | Comments discussing Prof. Doboli's teaching style and which courses he teaches | documents/dobolireddit1_cleaned.txt |
| 7 | Reddit r/SBU — "Dear Alex Doboli" thread | Open-letter post about the AI/self-learning teaching style, plus a TA response | documents/dobolireddit2_cleaned.txt |
| 8 | Reddit r/SBU — "The new ESE 124 Professor" thread | Positive thread praising Doboli vs. other professors, with alumni/TA comments | documents/doboliredditgood.txt |
| 9 | Reddit r/SBU — "ESE124 — Doboli" thread | Mixed/neutral thread on the pre/post-COVID experience, with alumni and TA replies | documents/doboliredditneutral.txt |
| 10 | SBU Faculty Page | Factual background: appointment, education, research record, publications, h-index | documents/alexdooli.txt |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**
1 review/comment per chunk(Anywhere between 100-400 tokens)
**Overlap: 0**

**Reasoning:**
The documents consists of seperate reviews and comments from Reddit, Classie Evaluations, and RateMyProfessor. Each review is treated as its own chunk because it usually contains a complete opinion or experience. An overlap of 0 tokens is used since the reviews are not part of a continuous thought, and do not rely on surrounding chunks for context. This reduces duplicate information while improving retrieval precision by returning the most relevant reviews directly.
---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
all-MiniLM-L6-v2
**Top-k:**
k=5
**Production tradeoff reflection:**
all-MiniLM-L6-v2 was chosen because it is lightweight, fast, and provides strong semantic search performance for short text documents such as student reviews and comments. A top-k value of 5 balances retrieval quality and context size by returning enough relevant reviews without introducing excessive noise. In a production environment, larger embedding models could improve retrieval accuracy, especially for more complex or domain-specific queries, but would increase computational cost and latency.
---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**
The system prompt contains two explicit grounding rules, answering only with the student reviews provided in the context, and telling it to avoid outside or prior knowledge.On top of this, I specified that if the provided reviews do not contain enough information to answer, it should say it doesn't have enough information.

**How source attribution is surfaced in the response:**
Rather than trusting the model to name its sources, the source list is assembled from the retrieved chunk metadata and appended to every response automatically. The model is only asked to cite reviews by bracket number in its answer. The actual source names, like "SBU Course Evaluation — ESE 124," are filled in by the code. This way, the citations are always accurate and tied to what was actually retrieved, not what the model guessed.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 |What are students' general opinion on Professor Doboli? |Mixed-Negative. Some students say hes knoledgable and caring, but that his teaching style is hard to follow and is difficult for beginners |Mixed, some people like that he goes into the proofs instead of slides, but others felt it was lazy and just regurgitating things.  |Relevant |Accurate |
| 2 |Is ESE 124 with Doboli beginner-friendly? |Generally no, Professor Doboli teaches like you should know the class beforehand |Hedged: says it's an "easy A" if you're already good at coding and has a heavy workload, but concludes it is "unclear" whether the class is beginner-friendly. |Partially Relevant |Inaccurate |
| 3 |What are the biggest complaints of Professor Dobolis classes? |Unclear lectures, heavy reliance on self learning, and a pace not suitable for beginners |A lazy, textbook-heavy teaching style that feels redundant, a style that doesn't suit everyone, COVID-era disruption, and ESE 344 being too focused on LeetCode. |Partially Relevant |Partially accurate |
| 4 |How do students compare ESE 224 and 124 with Professor Doboli? |224 is just like 124, with slightly harder content and more focused on data structures. |224 is "more or less the same as ESE 124 but with more difficult content"; notes only one review directly compares the two. |Relevant|Acccurate |
| 5 |What is valuable about ESE124 with Professor Doboli? |Learning C fundamentals is nice, his labs give good hands-on support, and the final project connects things together. |The pre-lab videos, TA support and office hours, and the final project that ties the course together are the valuable parts; one review adds he does a good job teaching programming. |Relevant |Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
Is ESE 124 with Doboli beginner-friendly?

**What the system returned:**
It noted the class is an "easy A" if you already know coding and that the workload is heavy, but ultimately concluded it was "unclear" whether the course is beginner-friendly — the opposite of the expected directional "no." that was present in majority of the sources

**Root cause (tied to a specific pipeline stage):**
The failure is split across two stages. At the retrieval stage, `all-MiniLM-L6-v2` surfaced chunks about general difficulty and workload ("easy A if you already know coding") rather than the most directly relevant chunk from the ESE 124 course evaluation, which explicitly states: "this class is intended for complete beginners… I would have borderline failed if I came in with no coding experience." With only 53 chunks in the corpus and k=5, that one high-signal chunk was ranked outside the top 5 and dropped entirely. At the generation stage, the system prompt instructs the model to "reflect both positive and negative opinions when reviews disagree." The mixed retrieved context triggered that balancing behavior, causing the LLM to hedge rather than synthesize the stronger directional conclusion the corpus supports.

**What you would change to fix it:**
Increase k from 5 to 7–8 to reduce the chance of dropping high-signal chunks in a small corpus. We can also introduce a system where low relevance chunks are dropped, allowing the model to pull from a set of chunks with less noise and more relevant data.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**
Having the chunking strategy written out in advance made implementation straightforward. Because I had already decided that each review would be its own chunk with no overlap, there was no guesswork when writing the ingestion script. I knew exactly what the separator was, why I was using it, and what to filter out. Without that decision already made, I would have spent time experimenting with character counts or sliding windows that don't fit the structure of individual reviews.

**One way your implementation diverged from the spec, and why:**
The spec didn't mention any preprocessing beyond splitting on `---`. During implementation I realized that the document files had boilerplate header lines like `# Source: SBU Course Evaluation — ESE 124` at the top of every file, and those lines were ending up at the start of chunks. They weren't part of any review, so they were adding noise to retrieval. I added a step to strip those out before storing the chunks. It wasn't planned, but it was a quick fix once I saw the actual chunk output and realized the headers didn't belong there.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
     I told the AI to create a script to clean the documents I gave it. I gave it my chunking strategy and explained I would be using it for RAG preprocessing
- *What it produced:*
     It produced documents that were mostly clean, but still had some UI elements in it and did not filter out for noise and no clear seperation. THis would have made chunking very hard
- *What I changed or overrode:*
     I reorganized the documents so that only the most relevant comments/info stay on their, instead of conversational noise. I also grouped them more clearly so that the chunking process was easier. 

**Instance 2**

- *What I gave the AI:*
     I told the AI to create a prompt for Grok, giving it my grounding rules, what exactly im looking for, and told it to check the documents for a more accurate prompt
- *What it produced:*
     It generated a prompt that was mostly correct. However, if the model didn't know the answer to something, it would just make something up.
- *What I changed or overrode:*
     I added the "If the provided reviews do not contain enough information to answer, say exactly: "I don't have enough information in the reviews to answer that."" This was important because now, it was able to cut through noise, and not have to make up answers for things it has no context for. 
