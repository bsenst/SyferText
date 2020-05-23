import syft as sy
import torch
import syfertext
from syft.generic.string import String
from syfertext.pointers.doc_pointer import DocPointer

import numpy as np

hook = sy.TorchHook(torch)
me = hook.local_worker

nlp = syfertext.load("en_core_web_lg", owner=me)


def test_avg_vector_valid_token():
    """Test that the average vector of valid tokens match the expected result"""

    doc = nlp("on your left")
    actual = doc.vector
    vectors = None

    # Count the tokens that have vectors
    vector_count = 0

    for token in doc:

        # Get the vector of the token if one exists
        if token.has_vector:

            # Increment the vector counter
            vector_count += 1

            # cumulate token's vector by summing them
            vectors = token.vector if vectors is None else vectors + token.vector

    # if no tokens with vectors were found, just get the default vector (zeros)
    if vector_count == 0:

        expected_vector = doc.vocab.vectors.default_vector

    else:

        # Create the final Doc vector
        expected_vector = vectors / vector_count

    # assert that actual and expected results match
    assert (actual == expected_vector).all()


def test_avg_vector_non_valid():
    """Test that the average vector of invalid tokens match the expected result"""

    doc = nlp("non-valid-token")
    actual = doc.vector
    vectors = None

    # Count the tokens that have vectors
    vector_count = 0

    for token in doc:

        # Get the vector of the token if one exists
        if token.has_vector:

            # Increment the vector counter
            vector_count += 1

            # cumulate token's vector by summing them
            vectors = token.vector if vectors is None else vectors + token.vector

    # if no tokens with vectors were found, just get the default vector (zeros)
    if vector_count == 0:

        expected_vector = doc.vocab.vectors.default_vector

    else:

        # Create the final Doc vector
        expected_vector = vectors / vector_count

    # assert that actual and expected results match
    assert (actual == expected_vector).all()


def test_add_custom_attr():
    """Test adding custom attributes to Doc & Token objects"""

    doc = nlp("Joey doesnt share food")
    token = doc[0]

    # add new custom attributes
    doc.set_attribute(name="doc_tag", value="doc_value")
    token.set_attribute(name="token_tag", value="token_value")

    # check if custom attributes have been added
    assert hasattr(doc._, "doc_tag") and doc._.doc_tag == "doc_value"
    assert hasattr(token._, "token_tag") and token._.token_tag == "token_value"


def test_check_custom_attr():
    """Test if Doc and Token custom attributes exist"""

    doc = nlp("Joey doesnt share food")
    token = doc[0]

    # add new custom attributes
    doc.set_attribute(name="doc_tag", value="doc_value")
    token.set_attribute(name="token_tag", value="token_value")

    # check if the custom attributes exist
    assert doc.has_attribute("doc_tag")
    assert token.has_attribute("token_tag")


def test_remove_custom_attr():
    """Test the deletion of a custom Doc attribute"""

    doc = nlp("Joey doesnt share food")
    token = doc[0]

    # add new custom attributes
    doc.set_attribute(name="doc_tag", value="doc_value")
    token.set_attribute(name="token_tag", value="token_value")

    # remove the new custom attributes
    doc.remove_attribute(name="doc_tag")
    token.remove_attribute(name="token_tag")

    # Verify they do were removed
    assert (not doc.has_attribute("doc_tag")) and (not token.has_attribute("token_tag"))


def test_update_custom_attr_doc():
    """Test updating custom attribute of Doc objects"""

    doc = nlp("Joey doesnt share food")

    # add new custom attribute
    doc.set_attribute(name="my_custom_tag", value="tag")

    # check custom attribute has been added
    assert hasattr(doc._, "my_custom_tag") and doc._.my_custom_tag == "tag"

    # now update the attribute
    doc.set_attribute(name="my_custom_tag", value="new_tag")

    # now check the updated attribute
    assert hasattr(doc._, "my_custom_tag") and doc._.my_custom_tag == "new_tag"


def test_exclude_tokens_on_attr_values_doc():
    """Test that the get_vector method ignores tokens based on the excluded_tokens dict"""

    doc = nlp("Joey never ever share food")
    doc_excluding_tokens = nlp("Joey never share food")

    # add custom_attr to the last token, the word ever
    token = doc[2]
    token.set_attribute(name="attribute1_name", value="value1")

    # initialize the excluded_tokens dict
    excluded_tokens = {"attribute1_name": {"value1", "value2"}, "attribute2_name": {"v1", "v2"}}

    # checks if get_vector returns the same vector for doc and the doc with the word to exclude already missing,
    # all() is needed because equals for numpy arrays returns an array of booleans.
    assert all(doc.get_vector(excluded_tokens) == doc_excluding_tokens.get_vector())

    # checks if get_vector without excluded_tokens returns a different vector for doc
    # and doc with the word to exclude already missing.
    assert any(doc.get_vector() != doc_excluding_tokens.get_vector())


def test_get_token_vectors():
    """Test the get_token_vectors method"""

    doc = nlp("Joey never ever share food")
    doc_excluding_tokens = nlp("Joey never share food")

    # add custom_attr to the last token, the word `ever`
    token = doc[2]
    token.set_attribute(name="attribute1_name", value="value1")

    # initialize the excluded_tokens dict
    excluded_tokens = {"attribute1_name": {"value1", "value2"}, "attribute2_name": {"v1", "v2"}}

    # checks the number of vectors after ignoring the excluded tokens
    assert (
        doc.get_token_vectors(excluded_tokens).shape[0]
        == doc_excluding_tokens.get_token_vectors().shape[0]
    )

    # checks the shape of the returned tensor
    assert doc.get_token_vectors(excluded_tokens).shape[0] == 4
    assert doc.get_token_vectors().shape[0] == 5


def test_ownership_doc_local():
    """Tests that the doc object created on the local worker is owned by the local worker itself"""

    # create a local doc object
    doc = nlp("we were on a break")

    # test the doc owner is the local worker
    assert doc.owner == me


def test_ownership_doc_remote():
    """Tests that the doc object pointed by doc pointer is owned by remote worker"""

    # create a remote worker
    bob = sy.VirtualWorker(hook=hook, id="bob")

    # get a String Pointer
    text_ptr = String("we were on a break").send(bob)

    # create a doc pointer
    doc = nlp(text_ptr)

    # check owner of the doc pointer
    assert doc.owner == me

    # check owner of doc object pointed by the `doc` DocPointer
    assert bob._objects[doc.id_at_location].owner == bob


def test_nbor():
    """Test that neighbor selections return the correct tokens"""

    doc = nlp("Joey doesnt share food")

    # Select a sample token at position `2`
    token = doc[2]

    # Test indices ranging from `-2` to `1`
    nbor_ids = range(-2, 2)

    assert all([doc[idx].text == token.nbor(offset).text for idx, offset in enumerate(nbor_ids)])
