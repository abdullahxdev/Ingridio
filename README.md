# Ingridio

Ingridio is an AI-powered cooking app built for one simple moment: opening your fridge and not knowing what to make.

Take a photo of your fridge, pantry shelf, or countertop ingredients, and Ingridio uses computer vision plus recipe intelligence to generate practical meals from what you already have.

## Why Ingridio

Most recipe apps start with a search bar. Ingridio starts with reality.

- You have ingredients, not a perfect grocery list.
- You need fast options, not endless scrolling.
- You want less waste, lower food spend, and better meals.

Ingridio turns ingredient chaos into a clear cooking plan.

## Core Experience

1. **Snap** a photo of your fridge or ingredients.
2. **Detect** items with computer vision.
3. **Refine** what Ingridio found (add, remove, rename, quantities).
4. **Generate** recipes tailored to your available ingredients.
5. **Cook** with step-by-step instructions.

## Key Features

- **Fridge Vision Scan**  
  Detects ingredients directly from camera photos.

- **AI Recipe Generation**  
  Builds meal options based on detected and selected ingredients.

- **Use-What-You-Have Mode**  
  Prioritizes recipes requiring little to no additional shopping.

- **Smart Substitutions**  
  Suggests alternatives when ingredients are missing.

- **Leftover Rescue**  
  Converts nearly-expiring items into practical meals.

- **Diet and Allergy Controls**  
  Filters recipes by dietary goals and restrictions.

- **Time and Skill Filters**  
  Finds meals by prep time, complexity, and equipment.

- **Portion and Macro Awareness**  
  Adapts recipes for servings and nutrition targets.

- **Personal Taste Profile**  
  Learns preferences over time to improve recommendations.

- **Weekly Meal Suggestions**  
  Turns current inventory into a short meal plan.

- **Auto Grocery Top-Up**  
  Generates a minimal shopping list for missing ingredients.

- **Cost-Aware Cooking**  
  Highlights lower-cost recipe paths when possible.

## Product Principles

- **Practical over perfect**: useful suggestions in real kitchens.
- **Fast over complicated**: decisions in seconds, not minutes.
- **Waste less**: prioritize ingredients you already own.
- **Personal by default**: adapt to your diet, routine, and taste.

## Tech Stack

- **Framework**: Flutter
- **Language**: Dart
- **Platform Targets**: Mobile and web (project scaffolded for Android, iOS, and web)

## Local Development

### Prerequisites

- Flutter SDK installed and available in PATH
- Dart SDK (included with Flutter)

### Run

```bash
flutter pub get
flutter run
```

### Test

```bash
flutter test
```

## Current Project Status

This repository currently contains the Ingridio Flutter application scaffold and is positioned for rapid feature implementation.

## Roadmap Highlights

- Ingredient detection from live camera and gallery uploads
- Confidence scoring and ingredient correction UX
- Recipe ranking by ingredient match, cook time, and nutrition fit
- Personalized recommendation loop based on user feedback
- Pantry tracking with expiration-aware suggestions
- In-app grocery integrations and shopping optimization


