# GrowMate Architecture

## Route to Template to Function Map

```mermaid
flowchart TD
    A[/ /] --> A1[index.html]
    A1 --> A2[home]

    B[/login GET|POST/] --> B1[login.html]
    B1 --> B2[login]
    B2 --> B3[Firebase token verify]
    B2 --> B4[Firestore user upsert]

    C[/signup GET|POST/] --> C1[signup.html]
    C1 --> C2[signup]
    C2 --> C3[Firebase token verify]
    C2 --> C4[Firestore profile upsert]

    D[/disease-detection GET/] --> D1[disease_detection.html]
    E[/disease-detection POST/] --> E1[result.html]
    E1 --> E2[analyze_plant_disease]
    E2 --> E3[get_gemini_analysis]
    E3 --> E4[save_disease_analysis]

    F[/analyze POST/] --> F1[analyze]
    F1 --> F2[analyze_plant_disease]
    F2 --> F3[save_disease_analysis]

    G[/farm-management GET|POST/] --> G1[farm_management.html]
    G1 --> G2[farm_management]
    G2 --> G3[get_farm_recommendations]
    G3 --> G4[fetch_gemini_response]
    G4 --> G5[save_farm_recommendation]

    H[/chatbot GET|POST/] --> H1[chatbot.html]
    H1 --> H2[chatbot]
    H2 --> H3[get_chat_messages]
    H2 --> H4[get_gemini_reply]
    H4 --> H5[fetch_gemini_response]
    H2 --> H6[save_chat_message]

    I[/about_us/] --> I1[about_us.html]
    I1 --> I2[about_us]

    J[/test-auth/] --> J1[test_auth]
    J1 --> J2[Firebase app health]

    K[/robots.txt/] --> K1[static/Robots.txt]
    L[/sitemap.xml/] --> L1[static/sitemap.xml]
```

## Data Persistence

- Auth identity source: Firebase Auth ID tokens
- User profile store: Firestore `users/{uid}`
- Chat history store: Firestore `users/{uid}/chat_sessions/{sessionId}/messages/{messageId}`
- Disease analysis store: Firestore `users/{uid}/analysis_history/{id}`
- Farm recommendation store: Firestore `users/{uid}/farm_recommendations/{id}`

## Legacy Archive

Legacy paths moved to `legacy_backup/` for safe rollback.
