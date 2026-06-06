from prism.core.footnotes import TermFootnote, insert_footnote_markers


def test_insert_footnotes_first_occurrence_only_and_document_order():
    report = (
        "# Report\n\n"
        "Free cash flow improved while the P/E ratio contracted.\n\n"
        "Later, free cash flow was mentioned again and P/E ratio appeared again."
    )
    terms = [
        TermFootnote(
            term="P/E ratio",
            surface_form="P/E ratio",
            definition="The price-to-earnings ratio compares a company's share price with its earnings per share.",
        ),
        TermFootnote(
            term="free cash flow",
            surface_form="free cash flow",
            definition="Free cash flow is cash generated after operating expenses and capital spending.",
        ),
    ]

    result = insert_footnote_markers(report, terms)

    assert "Free cash flow[^1] improved while the P/E ratio[^2] contracted." in result
    assert "Later, free cash flow was mentioned again and P/E ratio appeared again." in result
    assert result.count("free cash flow[^") == 0
    assert result.count("P/E ratio[^") == 1
    assert "[^1]: Free cash flow is cash generated after operating expenses and capital spending." in result
    assert "[^2]: The price-to-earnings ratio compares a company's share price with its earnings per share." in result


def test_insert_footnotes_deduplicates_terms_by_surface_form():
    report = "Revenue grew, and revenue quality improved."
    terms = [
        TermFootnote(term="revenue", surface_form="Revenue", definition="Revenue is total sales before expenses."),
        TermFootnote(term="Revenue", surface_form="Revenue", definition="Duplicate definition should not be used."),
    ]

    result = insert_footnote_markers(report, terms)

    assert result.count("Revenue[^1]") == 1
    assert "Duplicate definition should not be used" not in result
    assert "[^1]: Revenue is total sales before expenses." in result
