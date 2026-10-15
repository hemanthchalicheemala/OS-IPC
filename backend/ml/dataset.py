"""Small labeled dataset for message classification (normal/spam/toxic/urgent)."""

from __future__ import annotations


def get_training_samples() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []

    normal = [
        "Hello, how are you doing today?",
        "Can we meet at 3pm to discuss the project?",
        "Please review the attached notes when you can.",
        "Thanks for your help with the assignment.",
        "The meeting has been moved to room 204.",
        "I finished the report and shared it on Drive.",
        "Looking forward to collaborating on this task.",
        "Reminder: submit your weekly update by Friday.",
        "The code review comments look good overall.",
        "Let us sync tomorrow morning about IPC metrics.",
        "Great work on the dashboard charts.",
        "I will push the latest commits after lunch.",
        "Could you clarify the requirements for shared memory?",
        "The documentation is updated in the README.",
        "Enjoy your weekend and rest well.",
    ]

    spam = [
        "Congratulations! You won a FREE iPhone click now!!!",
        "URGENT: claim your lottery prize immediately $$$",
        "Buy cheap meds online, limited offer, act now!",
        "You have been selected for a cash reward, verify account",
        "Hot singles in your area want to chat, click here",
        "Make $5000/week working from home, no experience needed",
        "Your package is held, pay customs fee at this link",
        "Crypto giveaway: double your Bitcoin today only",
        "Exclusive deal: 90% OFF luxury watches, buy now",
        "Nigerian prince needs your bank details urgently",
        "Free gift card waiting — confirm your password",
        "Weight loss miracle pills, doctor hated this trick",
    ]

    toxic = [
        "You are an idiot and your code is garbage",
        "Shut up, nobody cares about your stupid opinion",
        "I hate this project and everyone working on it",
        "What a worthless teammate, do us a favor and quit",
        "This is the dumbest idea I have ever heard",
        "Get lost, you incompetent fool",
        "Your message is trash and so are you",
        "Stop wasting our time with this nonsense, moron",
    ]

    urgent = [
        "URGENT: production server is down, need help ASAP",
        "Critical security patch required within the hour",
        "Emergency: database backup failed, escalate now",
        "ASAP please review the failing CI build",
        "Immediate action needed: disk space critically low",
        "Priority P0: customer-facing API returning 500s",
        "Time-sensitive: submit viva slides before 10am",
        "Alert: memory leak causing OOM, restart required now",
    ]

    for t in normal:
        texts.append(t)
        labels.append("normal")
    for t in spam:
        texts.append(t)
        labels.append("spam")
    for t in toxic:
        texts.append(t)
        labels.append("toxic")
    for t in urgent:
        texts.append(t)
        labels.append("urgent")

    return texts, labels


def get_sentiment_samples() -> tuple[list[str], list[str]]:
    positive = [
        "I love this project, it works brilliantly!",
        "Excellent progress, great teamwork today.",
        "This feature makes me really happy.",
        "Fantastic results on the latency benchmarks.",
        "Thank you, that was very helpful and kind.",
    ]
    negative = [
        "This is terrible and frustrating to use.",
        "I am disappointed with the broken build.",
        "Awful performance, everything feels slow.",
        "I hate how unreliable this keeps failing.",
        "Horrible experience debugging these crashes.",
    ]
    neutral = [
        "The process started with PID 1234.",
        "Message sent using the pipe mechanism.",
        "Shared memory buffer size is 65536 bytes.",
        "Experiment completed in 1200 milliseconds.",
        "Queue depth is currently five items.",
    ]
    texts: list[str] = []
    labels: list[str] = []
    for t in positive:
        texts.append(t)
        labels.append("positive")
    for t in negative:
        texts.append(t)
        labels.append("negative")
    for t in neutral:
        texts.append(t)
        labels.append("neutral")
    return texts, labels
