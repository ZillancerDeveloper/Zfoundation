from datetime import datetime

from foundation.models import CurrencyRate


def currency_convert(amount, base_currency, to_currency):
    if base_currency != to_currency:
        try:
            rate_objs = CurrencyRate.objects.filter(
                currency_from=base_currency,
                currency_to=to_currency,
                effective_date__lte=datetime.now(),
            )
            if rate_obj := rate_objs.latest():
                amount = rate_obj.buy_rate * amount
        except CurrencyRate.DoesNotExist:
            pass
        except:
            # reverse
            rate_objs = CurrencyRate.objects.filter(
                currency_from=to_currency,
                currency_to=base_currency,
                effective_date__lte=datetime.now(),
            )
            if rate_obj := rate_objs.latest():
                amount = (1 / rate_obj.buy_rate) * amount

    return amount
