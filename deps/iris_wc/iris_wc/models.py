from django.db import models
from django.utils.translation import gettext_lazy as _

from iris.app.models import CancelableMixin, NotesMixin, TimestampMixin, add_note_type


class Order(TimestampMixin, CancelableMixin, NotesMixin, models.Model):
    wc_order_id = models.IntegerField(_("WooCommerce order ID"))
    wc_order_notes = models.TextField(_("WooCommerce order notes"), blank=True)

    def cancel(reason):
        super().cancel(reason)
        for line in self.lines.all():
            line.cancel(reason)

    def __str__(self):
        return str(_(f"WooCommerce order {self.wc_order_id}"))


add_note_type("WooCommerce order", "iris_wc.Order")


class WooCommerceCategoryMixin(models.Model):
    wc_category_id = models.IntegerField(_("WooCommerce category ID"))

    class Meta:
        abstract = True


class Line(
    TimestampMixin, CancelableMixin, NotesMixin, WooCommerceCategoryMixin, models.Model
):
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="lines")
    category = models.ForeignKey(
        "iris.Category",
        on_delete=models.SET_NULL,
        related_name="woocommerce_lines",
        null=True,
        blank=True,
    )
    wc_order_item_id = models.IntegerField(_("WooCommerce order line ID"))

    def __str__(self):
        return str(
            _(
                f"WooCommerce line {self.wc_order_item_id} for order {self.order.wc_order_id}"
            )
        )


add_note_type("WooCommerce line", "iris_wc.Line")


class ProductMap(models.Model):
    wc_product_id = models.IntegerField(_("WooCommerce order ID"))
    category = models.ForeignKey(
        "iris.Category",
        on_delete=models.CASCADE,
        related_name="mapped_woocommerce_products",
    )

    def __str__(self):
        return str(
            _(
                f"Map: WooCommerce product {self.wc_product_id} -> Category {self.category}"
            )
        )


class CategoryMap(WooCommerceCategoryMixin, models.Model):
    category = models.ForeignKey(
        "iris.Category",
        on_delete=models.CASCADE,
        related_name="mapped_woocommerce_categories",
    )

    def __str__(self):
        return str(
            _(
                f"Map: WooCommerce category {self.wc_category_id} -> Category {self.category}"
            )
        )
