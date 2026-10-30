/**
 * Single place for institution details and public copy that appears across pages.
 * Edit here instead of hunting through components.
 */
export const site = {
  name: 'Kepler College',
  product: 'Knowledge Assistant',
  city: 'Kigali, Rwanda',
  // Confirm this address is the right public contact before launch.
  email: 'info@keplercollege.ac.rw',
  studentDomain: 'keplercollege.ac.rw',
}

/** Illustrative conversation shown on the landing page. Replace with a real one from your handbook. */
export const sampleConversation = {
  question: 'What happens if I miss an exam?',
  answer:
    'Contact your instructor and the registrar as soon as you can, and bring supporting evidence. The handbook sets a deadline for requesting a make-up exam.',
  source: 'Student Handbook',
}

/** Suggested first questions in the chat, by role. */
export const suggestedQuestions: Record<string, string[]> = {
  student: [
    'What are the rules on class attendance?',
    'How do I appeal a grade or a decision?',
    'Summarise the student handbook for a new student',
  ],
  staff: [
    'What is the procedure for requesting leave?',
    'Summarise the latest policy changes',
    'Which procedures apply to student discipline?',
  ],
  board_member: [
    'Summarise the college governance policies',
    'What reports are staff expected to submit?',
    'Which policies were updated most recently?',
  ],
  admin: [
    'List the policies available to staff',
    'Summarise the student handbook',
    'What procedures cover document retention?',
  ],
}
