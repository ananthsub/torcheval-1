# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

from typing import List, Optional

import torch

from sklearn.metrics import precision_recall_curve
from torch.nn import functional as F

from torcheval.metrics import BinaryPrecisionRecallCurve, MulticlassPrecisionRecallCurve
from torcheval.utils.test_utils.metric_class_tester import (
    BATCH_SIZE,
    MetricClassTester,
    NUM_TOTAL_UPDATES,
)


class TestBinaryPrecisionRecallCurve(MetricClassTester):
    def _test_binary_precision_recall_curve_class_with_input(
        self,
        input: torch.Tensor,
        target: torch.Tensor,
    ) -> None:
        input_tensors = input.reshape(-1, 1)
        target_tensors = target.reshape(-1)

        precision, recall, thresholds = _test_helper(input_tensors, target_tensors)

        compute_result = (precision, recall, thresholds)
        self.run_class_implementation_tests(
            metric=BinaryPrecisionRecallCurve(),
            state_names={"inputs", "targets"},
            update_kwargs={
                "input": input,
                "target": target,
            },
            compute_result=compute_result,
        )

    def test_binary_precision_recall_curve_class_base(self) -> None:
        input = torch.rand(NUM_TOTAL_UPDATES, BATCH_SIZE)
        target = torch.randint(high=2, size=(NUM_TOTAL_UPDATES, BATCH_SIZE))
        self._test_binary_precision_recall_curve_class_with_input(input, target)

        input = torch.rand(NUM_TOTAL_UPDATES, BATCH_SIZE)
        target = torch.randint(high=2, size=(NUM_TOTAL_UPDATES, BATCH_SIZE))
        self._test_binary_precision_recall_curve_class_with_input(input, target)

    def test_binary_precision_recall_curve_class_update_input_shape_different(
        self,
    ) -> None:
        num_classes = 2
        update_input = [
            torch.rand(5),
            torch.rand(8),
            torch.rand(2),
            torch.rand(5),
        ]

        update_target = [
            torch.randint(high=num_classes, size=(5,)),
            torch.randint(high=num_classes, size=(8,)),
            torch.randint(high=num_classes, size=(2,)),
            torch.randint(high=num_classes, size=(5,)),
        ]

        compute_result = _test_helper(
            torch.cat(update_input, dim=0),
            torch.cat(update_target, dim=0),
        )

        self.run_class_implementation_tests(
            metric=BinaryPrecisionRecallCurve(),
            state_names={"inputs", "targets"},
            update_kwargs={
                "input": update_input,
                "target": update_target,
            },
            compute_result=tuple(compute_result),
            num_total_updates=4,
            num_processes=2,
        )

    def test_binary_precision_recall_curve_class_invalid_input(self) -> None:
        metric = BinaryPrecisionRecallCurve()
        with self.assertRaisesRegex(
            ValueError,
            "input should be a one-dimensional tensor, "
            r"got shape torch.Size\(\[3, 2\]\).",
        ):
            metric.update(torch.rand(3, 2), torch.rand(3))

        with self.assertRaisesRegex(
            ValueError,
            "target should be a one-dimensional tensor, "
            r"got shape torch.Size\(\[3, 2\]\).",
        ):
            metric.update(torch.rand(3), torch.rand(3, 2))

        with self.assertRaisesRegex(
            ValueError,
            "The `input` and `target` should have the same shape, "
            r"got shapes torch.Size\(\[4\]\) and torch.Size\(\[3\]\).",
        ):
            metric.update(torch.rand(4), torch.rand(3))


class TestMulticlassPrecisionRecallCurve(MetricClassTester):
    def _test_multiclass_precision_recall_curve_class_with_input(
        self,
        input: torch.Tensor,
        target: torch.Tensor,
        num_classes: Optional[int] = None,
    ) -> None:
        if num_classes is None and input.ndim == 2:
            num_classes = input.shape[1]
        input_tensors = input.reshape(-1, 1)
        target_tensors = target.reshape(-1)
        assert isinstance(num_classes, int)
        input_tensors = input.reshape(-1, num_classes)
        target_tensors = target.reshape(-1)
        precision, recall, thresholds = [], [], []
        target_tensors = F.one_hot(target_tensors, num_classes=num_classes)
        for idx in range(num_classes):
            p, r, t = _test_helper(
                input_tensors[:, idx],
                target_tensors[:, idx],
            )
            precision.append(p)
            recall.append(r)
            thresholds.append(t)

        compute_result = (precision, recall, thresholds)
        self.run_class_implementation_tests(
            metric=MulticlassPrecisionRecallCurve(num_classes=num_classes),
            state_names={"inputs", "targets"},
            update_kwargs={
                "input": input,
                "target": target,
            },
            compute_result=compute_result,
        )

    def test_multiclass_precision_recall_curve_class_base(self) -> None:
        num_classes = 4
        input = torch.rand(NUM_TOTAL_UPDATES, BATCH_SIZE, num_classes)
        target = torch.randint(high=num_classes, size=(NUM_TOTAL_UPDATES, BATCH_SIZE))
        self._test_multiclass_precision_recall_curve_class_with_input(
            input, target, num_classes=num_classes
        )

    def test_multiclass_precision_recall_curve_class_label_not_exist(self) -> None:
        num_classes = 4
        input = torch.rand(NUM_TOTAL_UPDATES, BATCH_SIZE, num_classes)
        target = torch.randint(
            high=num_classes - 1, size=(NUM_TOTAL_UPDATES, BATCH_SIZE)
        )
        self._test_multiclass_precision_recall_curve_class_with_input(
            input, target, num_classes=num_classes
        )

        num_classes = 8
        input = torch.rand(NUM_TOTAL_UPDATES, BATCH_SIZE, num_classes)
        target = torch.randint(
            high=num_classes - 2, size=(NUM_TOTAL_UPDATES, BATCH_SIZE)
        )
        self._test_multiclass_precision_recall_curve_class_with_input(
            input, target, num_classes=num_classes
        )

    def test_multiclass_precision_recall_curve_class_update_input_shape_different(
        self,
    ) -> None:
        num_classes = 3
        update_input = [
            torch.rand(5, num_classes),
            torch.rand(8, num_classes),
            torch.rand(2, num_classes),
            torch.rand(5, num_classes),
        ]

        update_target = [
            torch.randint(high=num_classes, size=(5,)),
            torch.randint(high=num_classes, size=(8,)),
            torch.randint(high=num_classes, size=(2,)),
            torch.randint(high=num_classes, size=(5,)),
        ]

        input_tensors = torch.cat(update_input, dim=0)
        target_tensors = torch.cat(update_target, dim=0)
        target_tensors = F.one_hot(target_tensors, num_classes=num_classes)

        precision, recall, thresholds = [], [], []
        for idx in range(num_classes):
            p, r, t = _test_helper(
                input_tensors[:, idx],
                target_tensors[:, idx],
            )
            precision.append(p)
            recall.append(r)
            thresholds.append(t)

        compute_result = (precision, recall, thresholds)

        self.run_class_implementation_tests(
            metric=MulticlassPrecisionRecallCurve(),
            state_names={"inputs", "targets"},
            update_kwargs={
                "input": update_input,
                "target": update_target,
            },
            compute_result=tuple(compute_result),
            num_total_updates=4,
            num_processes=2,
        )

    def test_multiclass_precision_recall_curve_class_invalid_input(self) -> None:
        metric = MulticlassPrecisionRecallCurve(num_classes=4)
        with self.assertRaisesRegex(
            ValueError,
            "The `input` and `target` should have the same first dimension, "
            r"got shapes torch.Size\(\[4, 2\]\) and torch.Size\(\[3\]\).",
        ):
            metric.update(torch.rand(4, 2), torch.rand(3))

        with self.assertRaisesRegex(
            ValueError,
            "target should be a one-dimensional tensor, "
            r"got shape torch.Size\(\[3, 2\]\).",
        ):
            metric.update(torch.rand(3, 2), torch.rand(3, 2))

        with self.assertRaisesRegex(
            ValueError,
            r"input should have shape of \(num_sample, num_classes\), "
            r"got torch.Size\(\[3, 4\]\) and num_classes=2.",
        ):
            metric = MulticlassPrecisionRecallCurve(num_classes=2)
            metric.update(torch.rand(3, 4), torch.rand(3))


def _test_helper(
    input: torch.Tensor,
    target: torch.Tensor,
) -> List[torch.Tensor]:
    compute_result = precision_recall_curve(target, input)
    compute_result = [
        torch.tensor(x.copy(), dtype=torch.float32) for x in compute_result
    ]
    if torch.isnan(compute_result[1][0]):
        compute_result[1] = torch.tensor([1.0, 0.0], device=compute_result[1].device)
    return compute_result
