# HunarHub: PRD and Technical Overview

## 1. Problem
Cobblers, potters, tailors, artisans and small vendors have skills but little digital reach. They depend on foot traffic, word of mouth and middlemen, with no structured way to take requests or orders and no transparent pricing or availability.

## 2. Goals
- Connect local micro-entrepreneurs with nearby customers.
- Support service booking and product selling on one platform.
- Promote traditional skills and handmade products; reduce middleman dependence.

## 3. Users and roles
| Role | Can do |
|---|---|
| Customer | Register, browse and filter, view profiles, request services, buy products, see history, rate, report problems |
| Entrepreneur | Create profile, list services and products, accept or reject requests, confirm orders, set availability, see earnings |
| Admin | Approve entrepreneurs, manage categories, monitor orders and requests, resolve complaints, view analytics |

## 4. Scope
In scope: responsive web app, profiles and listings, product marketplace, request and order management.
Out of scope: native apps, international shipping, AI recommendations, logistics and delivery.

## 5. Key flows
1. Customer registers, browses by category, filters by skill, location and price.
2. Customer opens a profile, then requests a service or buys a product.
3. Entrepreneur accepts or rejects a request (or confirms an order), then marks it done.
4. Customer leaves a rating once work is completed.

## 6. Requirement coverage
| Requirement | Where |
|---|---|
| Registration, login, roles | `accounts/` |
| Browse, search, filter (skill, location, price) | `marketplace/views.py: browse` |
| Profiles, galleries, pricing | `entrepreneur_detail.html` |
| Service requests, product orders, history | `request_service`, `buy_product`, customer dashboard |
| Ratings and feedback | `add_review` (only after completed work) |
| Entrepreneur dashboard, availability, earnings | `entrepreneur_dashboard` |
| Admin approval, categories, monitoring, disputes, analytics | `admin_dashboard` and Django admin |

## 7. Data model
User (role, phone) 1-1 EntrepreneurProfile (category, location, is_verified, is_available) 1-N Service, Product.
Customer 1-N ServiceRequest (to a Service), Order (of a Product), Review (of an entrepreneur), Complaint.
Category 1-N EntrepreneurProfile.

## 8. KPIs (shown on the admin dashboard)
Registered entrepreneurs, active users (30 days), service request conversion rate, product sales volume and value, average entrepreneur earnings, average customer rating.

## 9. Non-functional notes
- Security: Django password hashing, CSRF protection on every form, role checks on every view, HTTPS and secure cookies when `DEBUG=0`.
- Performance: server-rendered pages, static files served by WhiteNoise; add DB indexes and caching as traffic grows.
- Reliability: stock is decremented in a transaction and restored on cancellation.
- Usability: mobile-first layout, plain-language labels.

## 10. Future enhancements
Mobile apps, digital payments and wallets, delivery integration, skill training and certification modules.
