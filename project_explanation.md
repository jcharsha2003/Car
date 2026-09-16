# Complete Project Walkthrough: Identification of Uninsured Vehicles

If you are new to Information Integration Architecture (IIA) and need to understand how this project works from top to bottom, this guide is for you! It is broken down into simple, easy-to-understand parts.

---

## Part 1: The Big Picture (What is this project?)

Imagine you are a police officer. You see a car on the road with the license plate **"UP32AB1234"**. You want to know:
1. Is the car insured?
2. Is it stolen?
3. Who owns it?
4. Are there any pending violations?

The problem is that the government doesn't have one giant "super database" with all this information. Instead, there are **five different departments**, and they all built their own databases completely separately:
- The **Traffic Department** has a database (`capture.db`) for their traffic cameras.
- The **Insurance Registry** has a database (`insurance.db`) for policies.
- The **Transport Office (RTO)** has a database (`registration.db`) for vehicle ownership.
- The **Police** have a database (`theft.db`) for stolen vehicles.
- The **Ministry** has a database (`ministry.db`) for filing violation reports.

**The Goal of this Project:** To build a central "brain" (called a **Mediator**) that takes one license plate number, automatically asks all 5 databases for their pieces of the puzzle, and pieces them together into one unified screen for the user.

---

## Part 2: The Core Problem — Schema Heterogeneity

Because the 5 departments built their databases in isolation, they didn't agree on what to call the license plate column!

- `capture.db` calls it `plate_number`
- `insurance.db` calls it `registration_id`
- `registration.db` calls it `vehicle_reg_no`
- `theft.db` calls it `vehicle_identifier`
- `ministry.db` calls it `vehicle_ref`

If you try to write a simple SQL query like `SELECT * FROM databases WHERE license_plate = 'UP32AB1234'`, it will fail because **none of the databases have a column named `license_plate`**.

This is called **Schema Heterogeneity**, and solving it is the whole point of Information Integration.

---

## Part 3: How We Solve the Problem (The Mediator)

We solve this using the **Mediator Architecture**. Here is exactly how it works, step-by-step, when you search for a vehicle in the app:

### Step 1: The Global Query
You type a plate number (e.g., `UP32AB1234`) into the Search box on the frontend. The frontend sends this to our backend Mediator.

### Step 2: Query Decomposition (Schema Mapping)
The Mediator holds a "dictionary" called the **GAV Mapping** (Global-As-View). It knows that the global concept is `registration_number`, and it knows what each database calls it.

The Mediator takes your one search and **decomposes** (splits) it into 5 different SQL queries:
1. It tells the capture database: `SELECT * WHERE plate_number = 'UP32AB1234'`
2. It tells the insurance database: `SELECT * WHERE registration_id = 'UP32AB1234'`
3. It tells the registration database: `SELECT * WHERE vehicle_reg_no = 'UP32AB1234'`
4. ...and so on.

### Step 3: Source Wrappers & Health Registry
Before sending the queries, the Mediator checks its **Source Registry**. This is a health monitor that constantly "pings" the 5 databases to see which ones are online and which ones are responding the fastest (e.g., in 0.5 milliseconds vs 1.2 milliseconds). 

The Mediator sends the 5 SQL queries through **Wrappers**. A wrapper is just a small piece of code that acts as a translator between our Mediator and the specific SQLite database file. 

### Step 4: Integration and Conflict Resolution
The 5 databases send their results back. The Mediator stitches them together into one big JSON object (the "Unified View"). 

While stitching, it checks for **Conflicts**. What if the Traffic Camera saw a "WHITE" car, but the RTO Registration database says the car is "SILVER"? The Mediator detects this semantic conflict and flags it so the user knows something is suspicious.

### Step 5: Overall Status Calculation
Finally, the Mediator looks at all the combined data and calculates the **Overall Status**. It uses a priority logic:
- If the Police database says it's **STOLEN**, the overall status is STOLEN.
- If it's not stolen, but the Insurance database says the policy is expired, the status is **INSURANCE_EXPIRED**.
- If there is no insurance record at all, the status is **UNINSURED**.
- If everything is perfect, the status is **INSURED**.

This final package of data is sent back to the React frontend, which displays the beautiful cards and status badges you see on the screen.

---

## Part 4: Advanced Feature — Schema Matching (Criterion 5)

How did the Mediator build that "dictionary" (the GAV mapping) in the first place? In a real-world scenario with 1,000 columns, humans can't map them manually.

Our project includes an advanced AI-like algorithm called **Multi-Signal Schema Matching** (based exactly on the IIA-3 lecture notes). If you give it two completely different column names (like `plate_number` and `vehicle_ref`), it uses 5 signals to figure out if they mean the same thing:

1. **Linguistic (N):** Are the words similar? (Uses Levenshtein edit distance and Jaccard overlaps).
2. **Instance-Based (I):** Do they contain the same data? It literally looks inside the databases. If `plate_number` contains "UP32AB1234" and `vehicle_ref` also contains "UP32AB1234", it scores a 100% overlap!
3. **Structural (S):** Do they sit next to similar columns in their tables?
4. **Constraint (C):** Are they both text fields? Are they both primary keys?
5. **Ontology (O):** Are they known synonyms?

By combining these scores (`Score = 0.35*N + 0.25*I + 0.20*S + 0.10*C + 0.10*O`), the algorithm automatically discovers that `plate_number` and `vehicle_ref` are actually the same thing, despite having totally different names.

---

## Part 5: The Frontend GUI

The frontend is built with **React** and **Vite**. It is what the user interacts with.

- **Dashboard:** Shows pie charts and stats (how many cars are insured vs uninsured).
- **Search Vehicle:** Where the magic happens. When you search, it shows the unified data, the status badge, and an **Execution Trace** at the bottom. The execution trace proves the SQL decomposition worked—it shows the exact query sent to each database and how many milliseconds it took.
- **Scan Vehicle (ANPR):** Simulates an ANPR camera. You upload a picture of a car, and a computer vision pipeline (YOLOv8 + EasyOCR) reads the license plate text out of the image, then automatically runs the Search on it.
- **Integration View:** An academic "under the hood" page. It shows you the architecture diagram, the GAV mapping tables, and the Schema Matching algorithm scores.

---

## Summary

1. We have 5 separate, differently-designed databases.
2. We map their columns together using Schema Matching.
3. A user searches a plate.
4. The Mediator splits the search into 5 unique SQL queries.
5. It gathers the data, resolves conflicts, and determines the vehicle's legal status.
6. The React GUI displays the results beautifully.
