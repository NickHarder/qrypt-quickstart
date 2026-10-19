//! The starter's one function, held to what it promises.

use qrypt_quickstart::greeting;

#[test]
fn greets_a_person_by_name_without_the_spaces_around_it() {
    assert_eq!(greeting("  Ada "), "Hello, Ada.");
}

#[test]
fn greets_a_plain_name_as_it_is() {
    assert_eq!(greeting("Ada"), "Hello, Ada.");
}
