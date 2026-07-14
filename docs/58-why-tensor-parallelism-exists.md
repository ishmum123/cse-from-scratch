# Why Tensor Parallelism Exists

## The Problem

One GPU cannot hold a model, but many can if the work is split.

## Challenge

Implement the smallest program that demonstrates 'Tensor Parallelism' before reading the solution.

## Exercise

Write a minimal implementation of 'Tensor Parallelism', then measure where it breaks.

---

## Engineering Notes

This discovery exists because the previous approach failed under a real constraint. The lesson is not 'Tensor Parallelism' as a fact, but as a response to pressure.

---

**Continue → Why MoE Exists**
