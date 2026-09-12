<img src="assets/hero.svg" alt="Muhammad Al-Shurman, backend-focused full-stack developer" width="100%" />

I build web platforms that hold up in production. Most of my work sits on the server side: REST APIs, relational data models, and the unglamorous work of keeping queries fast while the data keeps growing. Laravel and PostgreSQL do the heavy lifting, with Next.js and TypeScript on the interfaces that sit on top of them.

<a href="https://www.linkedin.com/in/muhammadalshorman/"><img src="https://img.shields.io/badge/LinkedIn-0B0E14?style=flat-square&logo=linkedin&logoColor=5B8DEF&labelColor=0B0E14" alt="LinkedIn" height="28" /></a>
<a href="https://www.upwork.com/freelancers/~01d6bfb05bb6575a3b"><img src="https://img.shields.io/badge/Upwork-0B0E14?style=flat-square&logo=upwork&logoColor=5B8DEF&labelColor=0B0E14" alt="Upwork" height="28" /></a>
<a href="mailto:your.email@example.com"><img src="https://img.shields.io/badge/Email-0B0E14?style=flat-square&logo=maildotru&logoColor=5B8DEF&labelColor=0B0E14" alt="Email" height="28" /></a>

## Stack

<img src="assets/stack.svg" alt="Backend: PHP, Laravel, Node.js, Express, REST APIs, background jobs. Frontend: Next.js, React, TypeScript, Tailwind CSS. Data: PostgreSQL, MySQL, Redis, query optimization. Platform: Docker, Nginx, Linux, Git, CI pipelines. Practice: clean architecture, service layer, automated testing, code review." width="100%" />

## Selected work

<table>
  <tr>
    <td width="50%" valign="top">
      <h3>abjd.store</h3>
      <p>A live e-commerce platform serving real customer traffic. I designed the catalog and order schema, built the API behind the storefront, and rewrote the heaviest listing and checkout queries so response times stayed flat as the catalog grew.</p>
      <p><code>Laravel</code> <code>PHP</code> <code>MySQL</code> <code>REST API</code></p>
    </td>
    <td width="50%" valign="top">
      <h3>Academic management system</h3>
      <p>A role-based academic workflow platform used by more than 176 students. Students, instructors and administrators move through the same records with different permissions, on a relational schema that keeps enrollment and grading data consistent.</p>
      <p><code>Laravel</code> <code>MySQL</code> <code>RBAC</code> <code>Blade</code></p>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h3>Enterprise operations portal</h3>
      <p>An internal corporate system for requests and multi-level approvals. Every action is permission-checked and recorded, so a request can be traced from submission to final sign-off without guesswork.</p>
      <p><code>Laravel</code> <code>PostgreSQL</code> <code>Docker</code> <code>MVC</code></p>
    </td>
    <td width="50%" valign="top">
      <h3>Booking marketplace</h3>
      <p>A reservation platform where availability, pricing and payment state have to agree at all times. Node and PostgreSQL on the backend, Next.js for the admin panel, with booking conflicts prevented at the database layer instead of in application code.</p>
      <p><code>Node.js</code> <code>Express</code> <code>Next.js</code> <code>PostgreSQL</code></p>
    </td>
  </tr>
</table>

## How I work

Schema first. Constraints and migrations enforce the rules, not application code that hopes for the best.

Read the query plan before blaming the framework. Most slow endpoints are a missing index or an N+1, not a language problem.

Ship small and reversible. Every migration has a way back, and every release stays small enough to reason about at 2 a.m.

## Activity

<img src="assets/stats.svg" alt="GitHub activity: commits, repositories, merged pull requests, stars and language distribution" width="100%" />
