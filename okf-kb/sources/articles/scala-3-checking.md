---
type: Article
title: Introduction to Scala 3's Capture Checking and Separation Checking
resource: https://virtuslab.com/blog/scala/introduction-to-scala-3-checking
timestamp: '2026-06-25T12:50:03Z'
---

Introduction to Scala 3's Capture Checking and Separation Checking   



  [Skip to main content](#maincontent)

* [Services](/services/)

  + [Expertise](/expertise/)

    - [Developer experience](/expertise/developer-experience/)
    - [IDE and Intellij](/expertise/ide-and-intelli-j-expertise/)
    - [Bazel monorepo](/expertise/monorepo-expertise-with-bazel/)
    - [ML ENGINEERING](/expertise/ml-engineering-services/)
    - [Gen AI](/expertise/gen-ai-software-development/)
    - [Scala consulting](/expertise/scala/)
    - [Scala Enterprise Support](/expertise/scala-enterprise-support)
    - [Next-Gen Systems  
      Integration](https://softwaremill.com/services/next-gen-systems-integration/)
  + [Software Engineering](/capabilities/)

    - [cloud engineering](/capabilities/cloud-native-engineering/)
    - [Platform engineering](/expertise/platform-engineering/)
    - [Secret management](https://virtuslab.com/expertise/secret-management/)
    - [Google cloud](/expertise/google-cloud-expertise/)
    - [Oracle Cloud Infrastructure](/expertise/oracle-cloud-infrastructure/)
    - [Data Engineering](/capabilities/data-engineering/)
    - [Frontend engineering](/capabilities/frontend-engineering/)
    - [Micro Frontends & Microservices](/expertise/micro-frontends-microservices/)
    - [Strapi CMS](/expertise/strapi-headless-cms-consulting/)
    - [Strapi MCP](/expertise/introducing-strapi-mcp/)
    - [Backend Engineering](/capabilities/backend/)
  + [Solutions](/services/)

    - [**VISDOM**](https://visdom.virtuslab.com/)
* [Industries](/sectors/)

  Industries Sectors

  + [Investment Banking](https://virtuslab.com/sectors/engineering-for-investment-banks)
  + [Financial Platforms](https://virtuslab.com/sectors/engineering-for-financial-platforms)
  + [Insurance](/sectors/insurance/)
  + [Logistics](/sectors/logistics-industry/)
  + [Industry 4.0](/sectors/industry-4-0/)
  + [Retail](/sectors/retail-industry/)

  Feature Reads

  + [![Unlock the power of your analytical data platform for data-driven decisions image](https://cdn.virtuslab.com/Unlock_the_power_of_your_analytical_data_platform_for_data_driven_decisions_92ea19ef71.jpg?format=webp&width=175)

    Unlock the power of your analytical data platform for data-driven decisions](/blog/data/analytical-data-platforms-data-driven-decisions)
  + [![what_is_developer_experience_cover_with_climbing_rocks](https://cdn.virtuslab.com/What_is_developer_experience_DX_image_min_c8c6854a52.jpg?format=webp&width=175)

    What is developer experience (DX) and how to tell if your project delivers a good one?](/blog/backend/what-is-developer-experience)
* [Insights](/blog/)
* [Resources](/blog/)

  Resources

  + [ARTICLES](/blog/)
  + [Business insights](/blog/business-insights/)
  + [Scala](/blog/scala/)
  + [Data Engineering](/blog/data/)
  + [Cloud Engineering](/blog/cloud/)
  + [Backend Engineering](/blog/backend/)
  + [Frontend Engineering](/blog/frontend/)
  + [Agent Visualization](/agent-visualization/)
  + [Success Stories](/success-stories/)
  + [Retail](/success-stories/industry/retail/)
  + [Industry 4.0](/success-stories/industry/industry-4-0/)
  + [Insurance & Fintech](/success-stories/industry/insurance-fintech/)
  + [Logistics](/success-stories/industry/logistics/)
  + [Media](/success-stories/industry/media-publishing/)
  + [Travel & Hospitality](/success-stories/industry/hospitality/)
  + [Healthcare](/success-stories/industry/healthcare/)

  Feature Reads

  + [![How_to_create_a_reference_architecture_with_Kubernetes_on_Azure_an_extensive_guide_image-min.jpg](https://cdn.virtuslab.com/How_to_create_a_reference_architecture_with_Kubernetes_on_Azure_an_extensive_guide_image_min_0a775b8613.jpg?format=webp&width=175)

    How to create a reference architecture with Kubernetes on Azure an extensive guide](/blog/cloud/reference-architecture-kubernetes-on-azure-guide)
  + [![How_to_build_an_LLM_chatbot_for_your_companys_information_image-min.jpg](https://cdn.virtuslab.com/How_to_build_an_LLM_chatbot_for_your_companys_information_image_min_efdd63125d.jpg?format=webp&width=175)

    How to build an LLM chatbot for your company’s information](/blog/ai/how-to-build-llm-chatbot)
* [Who we are](/about-us/)

  This Is VirtusLab

  + [About us

    Our mission is to continuously drive positive evolution in software technology.](/about-us/)
  + [COMMUNITY

    The community is an essential part of our effectiveness. We organize and sponsor tech events.](/community/)
  + [CAREERS

    Take your career to the next level. Become part of our team and choose flexibility and outstanding solutions.](https://careers.virtuslab.com/)
  + [Virtuslab Companies

    Committed to innovation, we strengthen relationships and add value for our customers, partners and team members.](https://lp.virtuslab.com/landings/vl-group/)
  + [COMPANY NEWS

    Contributions to open-source projects and events further enrich this vibrant community.](/company-news/)

[Contact usContact us](/contact)

 

* [Home](/)
* [blog](/blog)
* [scala](/blog/scala)
* [introduction to scala 3 checking](/blog/scala/introduction-to-scala-3-checking)

Introduction to Scala 3's Capture Checking and Separation Checking
==================================================================

![Picture of Rikito Taniguchi, Scala Compiler (Wasm/Native)](https://cdn.virtuslab.com/Rikito_image_c113328ea7.jpeg?format=webp&width=360)

Rikito Taniguchi

Scala Compiler (Wasm/Native)

Published: Apr 30, 2026|17 min read17 minutes read

![gold_and_purple](https://cdn.virtuslab.com/Ready_Rikito_cover_01509c710a.png?format=webp&width=768)

One of the trickiest parts of writing large-scale software is dealing with mutable data. For instance, data might be mutated in unexpected places, or resources might be used at the wrong timing.

Languages like Rust mitigate these problems through ownership and lifetimes. But how do we bring these ideas into a GC-based language like Scala in a way that doesn't break existing programs? In other words, we want to track access rights (capabilities) to resources (objects in the [object-capability model](https://en.wikipedia.org/wiki/Object-capability_model)), while leaving memory management to the GC.

Scala 3's answer is [Capture Checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html) + [Separation Checking](https://docs.scala-lang.org/scala3/reference/experimental/capture-checking/separation-checking.html).

[**Capture Checking**](#capture-checking)
-----------------------------------------

### **What is a "Capture"?**

Before explaining Capture Checking, let's start with what "capture" means.

This refers to closure capture. In the following program, the closure `increment` references `c`, which is defined outside the closure. We say that `increment` *captures* `c`.

Copy

Introduction to Scala 3's Capture Checking and Separation Checking

[Download full article](https://s3.eu-central-1.amazonaws.com/images.virtuslab.com/Scala_s_3_checking_36af52c6c4.pdf)

### **Capturing Types**

Capture Checking introduces **Capturing Types** to track variable captures at the type level.

`T^{x_1, ..., x_n}`

* `T`: the **shape type** — a value of this type captures the values in the following capture set
* `{x_1, ... x_n}`: the **capture set** — the set of values this value is allowed to capture

![Image Alt](https://cdn.virtuslab.com/capturing_types_c79a0517bc.png?format=webp&width=500)

For example, in the code above, `increment` has the following capturing type.

Copy

`Counter^` roughly means "`c` is a value tracked by capture checking."

And, you might wonder why `() -> Unit` instead of `() => Unit`. The `->` notation was introduced with capture checking.

* The traditional function type `A => B` represents a function that may capture arbitrary values.
* While the new `A -> B` represents a pure function that captures nothing.
* `A ->{c,d} B` is shorthand for `(A -> B)^{c,d}`, which means the function captures `c` and `d`.

See [Function Types | Capture Checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html#function-types) for details.

(`T^` is shorthand for `T^{any}`, where `any` is a top capability representing a separate, exclusive capability.)   
  
A value must have a non-empty capture set to be tracked by capture checking, so `any` is used to mark a value as being tracked. Although `c: Counter^ = new Counter` being able to "capture any capability" doesn't feel very intuitive, it is needed for the subtyping rules described later.

### **What Does Capture Checking Check?**

Capture Checking verifies that closures only capture values within their declared capture set. For example, the following program produces an error.

(The capture set of `increment` is `^{c1}`, but the closure body also captures `c2`, which is not in the set:)

Copy

Copy

This lets us express the constraint that `increment` can only operate on `c1` at the type level. Seen this way, the capture set (`^{c1}`) can be thought of as the set of capabilities that the closure is allowed to access.

(Subtyping is extended by capturing types: a type with a smaller capture set is a subtype. For example, `T^{} <: T^{c1} <: T^{c1,c2} <: T^{any}`. So assigning a value of type `() ->{c1,c2} Unit` to `() ->{c1} Unit` would be a type error.)

### **Example: Referentially Transparent Closures**

As a simple use case, let's implement a `map` that guarantees referential transparency — we want to ensure that the function passed to `map` doesn't perform any destructive mutations.

Copy

This prevents the function passed to `map` from accessing external mutable state.

### **Other Examples**

The reference documentation includes several more use cases. By treating values tracked by capture checking as capabilities, you can do things like effect tracking:

* [Escape Checking](https://docs.scala-lang.org/scala3/reference/experimental/cc.html#escape-checking)
* [Checked Exceptions](https://docs.scala-lang.org/scala3/reference/experimental/cc.html#checked-exceptions)

(This is the most commonly shown example of capture checking, but it's not the most intuitive one.)

### **Alias Tracking**

You might wonder whether aliases confuse capture checking, but they are tracked as well:

Copy

[**Separation Checking**](#separation-checking)
-----------------------------------------------

Capture Checking is an experimental feature that is getting closer to be stablized. [Separation Checking](https://docs.scala-lang.org/scala3/reference/experimental/capture-checking/separation-checking.html), on the other hand, is another experimental feature based on Capture Checking.

Capture Checking only tracks whether a value can be accessed. Separation Checking introduces `SharedCapability` (read-only) and `ExclusiveCapability` (writable) to track *which parts of the program can mutate data*. This helps prevent data races in concurrent programs and enables separate tracking of read-only vs. writable effects.

### **Mutable extends ExclusiveCapability**

Separation Checking provides `caps.Mutable`. Classes that extend it can define methods with the `update` modifier. An `update def` indicates that the method mutates the class's state (or external resources, whatever), and these methods cannot be called in a read-only context.

Copy

Here, `any` (`caps.any`) is a **top capability**, essentially the same as the universal capability (`cap`) from capture checking, but in separation checking each occurrence of `any` is treated as distinct and exclusive. (`any.rd` is the read-only version of `any`: it grants read access but prohibits mutation (i.e. calling `update` methods).)

(Each occurrence of `any` is treated as a separate, exclusive capability. For example, in `def swap(a: Ref^, b: Ref^)`, `a` gets `Ref^{any₁}` and `b` gets `Ref^{any₂}` — two distinct capabilities, so the compiler knows they don't alias each other.)

When writing parameter types, `Ref` expands to `Ref^{any.rd}`(read-only access). `Ref^` expands to `Ref^{any}` (full access including mutation).

Copy

Calling an update method inside `read` is not allowed:

Copy

### **The Separation Check**

Consider a `par` function that executes two functions in parallel. If one argument calls an update method on a resource, the other argument must not access that resource:

Copy

Copy

This constraint might seem overly strict. For a `seq` function that runs functions sequentially, such restrictions shouldn't be necessary. This is handled through a mechanism called *Hide*, which I'll explain next.

Copy

### **Move Semantics**

In Separation Checking, `T^` (`T^{any}`) represents a special type: an independent capability shared with no one.

Assigning a variable `y` to `T^` means that `y` is *hidden* by the exclusive capability `x`. As long as `x` is alive, the original `y` cannot be accessed (otherwise `x` and `y` would share the same capability).

This prevents unintended mutation through aliased references:

Copy

(Recall the `par` definition — its arguments also have the top capability `any`)

Copy

* When calling `par(() => r.set(1), () => r.set(2))`:
  + `() => r.set(1)` is hidden by `f` (transitively, `r` captured by this closure is also hidden by `f`)
  + `() => r.set(2)` tries to access `r`, but it's hidden by `f` — so this fails

This can be resolved by explicitly granting `g` access to the capabilities hidden by `f`:

Copy

(Previously called `cap` (the "universal capability"), now renamed to `any` and treated as a top capability in separation checking.)

### **Consume Parameters**

You might think you could bypass hiding by returning a `Ref^` from a function. Consider an in-place update function:

Copy

Returning a value with the top capability from a function is only safe if the parameter is no longer used (since the function might create and return an alias). So the `incr` definition above actually produces an error:

Copy

To compile this, the parameter must be marked with `consume`, explicitly indicating that the argument will be hidden (move semantics!):

Copy

[**Summary**](#summary)
-----------------------

Both Capture Checking and Separation Checking are still under active development, but they point toward a future where you can write Scala with GC-managed memory while selectively opting into Rust-like constraints where it matters. The best of both worlds.

**References**
--------------

* [Capture Checking - Bringing Effect Checking to the Masses](https://capless.cc/) — project page with links to papers
* [Capture Checking | Scala 3 Reference](https://docs.scala-lang.org/scala3/reference/experimental/cc.html)
* [Separation Checking | Scala 3 Reference](https://docs.scala-lang.org/scala3/reference/experimental/capture-checking/separation-checking.html)
* [System Capybara: Capture Tracking for Ownership and Borrowing | ICFP/SPLASH'25](https://2025.workshop.scala-lang.org/details/scala-2025/6/)

In this article

* [Capture Checking](#capture-checking)
* [Separation Checking](#separation-checking)
* [Summary](#summary)

Related articles

* [Comparing effect systems in Scala: The Problem and Future](/blog/scala/comparing-effect-systems-in-scala/)
* [Rethinking Gatling: A Scala CLI and Containerisation Approach to Performance Testing](/blog/scala/gatling-a-scala-cli/)
* [OOP vs. FP. The pursuit of extensibility part #1](/blog/scala/oop-vs-fp-the-pursuit-of-extensibility-part-1/)
* [Building Tools for an Unlimited Number of Edge Cases](/blog/scala/building-tools-for-an-unlimited-number-of-edge-cases/)

Article tags

* [#Trends](/blog/tag/trends)

[Previous article](/blog/scala/comparing-effect-systems-in-scala/ "Comparing effect systems in Scala: The Problem and Future")

[Next article](/blog/scala/our-impressions-from-the-scala-survey-2026/ "Our impressions from the Scala Survey 2026")

Explore more topics
-------------------

[![Image Alt](https://cdn.virtuslab.com/6_cover_ea58d787ee.jpg?format=webp&width=500)

### Comparing effect systems in Scala: The Problem and Future](/blog/scala/comparing-effect-systems-in-scala/)[![logos_gatling_Scala_cli_docker](https://cdn.virtuslab.com/Rethinking_Gatling_A_Scala_CLI_and_Containerization_Approach_to_Performance_Testing_cover_min_c29d6a6232.jpg?format=webp&width=500)

### Rethinking Gatling: A Scala CLI and Containerisation Approach to Performance Testing](/blog/scala/gatling-a-scala-cli/)[![OOP vs FP cover](https://cdn.virtuslab.com/OOP_vs_FP_cover_bbf7fa197c.jpg?format=webp&width=500)

### OOP vs. FP. The pursuit of extensibility part #1](/blog/scala/oop-vs-fp-the-pursuit-of-extensibility-part-1/)

![Image Alt](https://images.virtuslab.com/Tisax_footer_c54673144e.svg)![Image Alt](https://images.virtuslab.com/ISO_footer_5ed666e5c1.svg)

![Image Alt](https://images.virtuslab.com/Forbes2019_white_69059142a3.svg)

![Image Alt](https://images.virtuslab.com/Forbes2020_white_245ef35f87.svg)

![Image Alt](https://images.virtuslab.com/Forbes2022_white_08ce9e2a2b.svg)

![Image Alt](https://images.virtuslab.com/FT_2019_white_126dd04efc.svg)

![Image Alt](https://images.virtuslab.com/FT_2020_white_c3be149b52.svg)

![Image Alt](https://images.virtuslab.com/FT_2021_white_d6865a1156.svg)

![Image Alt](https://images.virtuslab.com/FT_2022_white_d5fd342c02.svg)

![Image Alt](https://images.virtuslab.com/Gazelle2018_white_b484d709cf.svg)

![Image Alt](https://images.virtuslab.com/Gazelle2020_white_a8fef2668c.svg)

![Image Alt](https://images.virtuslab.com/Gazelle2021_white_4fbf9b0e6f.svg)

* [Expertise](/expertise/)
* [Engagement](/services)
* [Capabilities](/capabilities/)
* [Success stories](/success-stories/)
* [About us](/about-us/)
* [Articles](/blog/)
* [Community](/community/)
* [Privacy Policy](/privacy-policy)

©2026 VirtusLab
