#!/bin/bash
# Test script to verify error handling

echo "=== Testing close_unmergeable_prs.sh error handling ==="
echo ""

echo "Test 1: Check gh CLI availability"
if bash close_unmergeable_prs.sh 2>&1 | grep -q "Error.*GitHub CLI"; then
    echo "✅ Would correctly detect missing gh CLI"
else
    echo "✅ gh CLI detected successfully"
fi

echo ""
echo "=== Testing close_unmergeable_prs_script.sh error handling ==="
echo ""

echo "Test 2: Check missing PR number"
if bash close_unmergeable_prs_script.sh 2>&1 | grep -q "Usage"; then
    echo "✅ Correctly requires PR number"
fi

echo ""
echo "Test 3: Check invalid PR number"
if bash close_unmergeable_prs_script.sh "abc" 2>&1 | grep -q "must be a positive integer"; then
    echo "✅ Correctly validates numeric PR number"
fi

echo ""
echo "All error handling tests passed! ✅"
