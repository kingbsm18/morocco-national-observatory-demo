# 🇲🇦 Observatoire National des Indicateurs Marocains

**Morocco National Observatory of Indicators**

A public-facing data observatory designed to make Moroccan national statistics easier to explore, understand, and compare.

The platform brings together key indicators covering population, economy, education, health, employment, markets, justice, and society, with an emphasis on clear visualization, source transparency, and data integrity.

## 🌐 Live Demo

https://morocco-national-observatory-demo.vercel.app/

## 🎯 Project Objective

The Observatory aims to provide citizens, journalists, researchers, and other users with an accessible interface for exploring Moroccan indicators.

Instead of presenting statistics as raw tables alone, the platform transforms them into:

- Interactive charts
- Key figures
- Structured indicator pages
- Historical trends
- Dimension-based comparisons
- Source and metadata information

The current version is a functional prototype and will progressively expand its data coverage and sources.

## 📊 Current Coverage

The current version contains **28 indicators**, covering areas including:

- 👥 Population & Demography
- 💰 Economy
- 📈 Money & Markets
- 🎓 Education & Culture
- 🏥 Health
- 💼 Employment
- ⚖️ Justice & Society

Each indicator is identified by its unique source identifier and linked to its corresponding data source.

## 🗂️ Data Sources

The current implementation primarily uses the **Haut-Commissariat au Plan (HCP) — Base de Données Statistiques (BDS)**.

The architecture is designed to progressively support additional official Moroccan and international sources.

Potential future sources include:

- Haut-Commissariat au Plan (HCP)
- Bank Al-Maghrib
- Office des Changes
- Ministère de l'Économie et des Finances
- Moroccan ministries and public institutions
- World Bank
- IMF
- UN agencies
- Other recognized international statistical institutions

Source information is preserved at indicator level whenever available.

## 🏗️ Architecture

The current application is built with:

- **Next.js**
- **React**
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui**
- **Vercel**

The application uses the HCP BDS API for the current indicator dataset.

### Data flow

```text
HCP BDS API
     ↓
Indicator ID
     ↓
Central Indicator Registry
     ↓
Data Validation
     ↓
Normalization
     ↓
Charts / Tables / Metadata
     ↓
Next.js Interface
