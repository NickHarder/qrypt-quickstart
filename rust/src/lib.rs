//! The project's Rust starter: one documented function and its test, so that the gate has
//! formatted, linted and tested code from the first commit. Replace it with the product's first
//! slice.

/// Says hello to someone by the name they give, without the spaces around it.
#[must_use]
pub fn greeting(person_name: &str) -> String {
    let trimmed_name = person_name.trim();
    format!("Hello, {trimmed_name}.")
}
