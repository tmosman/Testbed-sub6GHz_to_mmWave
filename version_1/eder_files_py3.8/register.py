import ederspi
import doc


class Register(ederspi.EderSpi):

    import device_info

    device_info = device_info.DeviceInfo()
    __instance = None

    regs =   {'chip_id':                 {'group':'system', 'addr':0x0000, 'size':4, 'value':0x02731803, 'mask':0xFFFFFFFF, 'doc':doc.chip_id_help},
              'chip_id_sw_en':           {'group':'system', 'addr':0x0004, 'size':1, 'value':0x00, 'mask':0x01, 'doc':doc.chip_id_sw_en_help},
              'fast_clk_ctrl':           {'group':'system', 'addr':0x0005, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.fast_clk_ctrl_help},
              'gpio_tx_rx_sw_ctrl':      {'group':'system', 'addr':0x0006, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_tx_rx_sw_ctrl_help},
              'gpio_agc_rst_ctrl':       {'group':'system', 'addr':0x0007, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_agc_rst_ctrl_help},
              'gpio_agc_start_ctrl':     {'group':'system', 'addr':0x0008, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_agc_start_ctrl_help},
              'gpio_agc_gain_in_ctrl':   {'group':'system', 'addr':0x0009, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.gpio_agc_gain_in_ctrl_help},
              'gpio_agc_gain_out_ctrl':  {'group':'system', 'addr':0x000a, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.gpio_agc_gain_out_ctrl_help},
              'bist_amux_ctrl':          {'group':'system', 'addr':0x000b, 'size':1, 'value':0x00, 'mask':0xCF, 'doc':doc.bist_amux_ctrl_help},
              'bist_ot_ctrl':            {'group':'system', 'addr':0x000d, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.bist_ot_ctrl_help},
              'bist_ot_temp':            {'group':'system', 'addr':0x000e, 'size':1, 'value':0x80, 'mask':0xDF, 'doc':doc.bist_ot_temp_help},
              'bist_ot_rx_off_mask':     {'group':'system', 'addr':0x000f, 'size':3, 'value':0x000000, 'mask':0x1FFFFF, 'doc':doc.bist_ot_rx_off_mask_help},
              'bist_ot_tx_off_mask':     {'group':'system', 'addr':0x0012, 'size':3, 'value':0x000000, 'mask':0x1FFFFF, 'doc':doc.bist_ot_tx_off_mask_help},
              'spare':                   {'group':'system', 'addr':0x001C, 'size':4, 'value':0xFF0000FF, 'mask':0xFFFFFFFF, 'doc':doc.spare_help},
              #
              'bias_ctrl':               {'group':'bias',   'addr':0x0020, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.bias_ctrl_help},
              'bias_vco_x3':             {'group':'bias',   'addr':0x0021, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.bias_vco_x3_help},
              'bias_pll':                {'group':'bias',   'addr':0x0022, 'size':1, 'value':0x00, 'mask':0x37, 'doc':doc.bias_pll_help},
              'bias_lo':                 {'group':'bias',   'addr':0x0023, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.bias_lo_help},
              'bias_tx':                 {'group':'bias',   'addr':0x0024, 'size':2, 'value':0x0000, 'mask':0xFFFF, 'doc':doc.bias_tx_help},
              'bias_rx':                 {'group':'bias',   'addr':0x0026, 'size':2, 'value':0x0000, 'mask':0x0FFF, 'doc':doc.bias_rx_help},
              #
              'pll_en':                  {'group':'pll',    'addr':0x0040, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.pll_en_help},
              'pll_divn':                {'group':'pll',    'addr':0x0041, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.pll_divn_help},
              'pll_pfd':                 {'group':'pll',    'addr':0x0042, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.pll_pfd_help},
              'pll_chp':                 {'group':'pll',    'addr':0x0043, 'size':1, 'value':0x00, 'mask':0x73, 'doc':doc.pll_chp_help},
              'pll_ld_mux_ctrl':         {'group':'pll',    'addr':0x0044, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.pll_ld_mux_ctrl_help},
              'pll_test_mux_in':         {'group':'pll',    'addr':0x0045, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.pll_test_mux_in_help},
              'pll_ref_in_lvds_en':      {'group':'pll',    'addr':0x0046, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.pll_ref_in_lvds_en_help},
              #
              'tx_ctrl':                 {'group':'tx',     'addr':0x0060, 'size':1, 'value':0x10, 'mask':0x7F, 'doc':doc.tx_ctrl_help},
              'tx_bb_q_dco':             {'group':'tx',     'addr':0x0061, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.tx_bb_q_dco_help},
              'tx_bb_i_dco':             {'group':'tx',     'addr':0x0062, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.tx_bb_i_dco_help},
              'tx_bb_phase':             {'group':'tx',     'addr':0x0063, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.tx_bb_phase_help},
              'tx_bb_gain':              {'group':'tx',     'addr':0x0064, 'size':1, 'value':0x00, 'mask':0x23, 'doc':doc.tx_bb_gain_help},
              'tx_bb_iq_gain':           {'group':'tx',     'addr':0x0065, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_bb_iq_gain_help},
              'tx_bfrf_gain':            {'group':'tx',     'addr':0x0066, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_bfrf_gain_help},
              'tx_bf_pdet_mux':          {'group':'tx',     'addr':0x0067, 'size':1, 'value':0x00, 'mask':0xBF, 'doc':doc.tx_bf_pdet_mux_help},
              'tx_alc_ctrl':             {'group':'tx',     'addr':0x0068, 'size':1, 'value':0x00, 'mask':0xF3, 'doc':doc.tx_alc_ctrl_help},
              'tx_alc_loop_cnt':         {'group':'tx',     'addr':0x0069, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_loop_cnt_help},
              'tx_alc_start_delay':      {'group':'tx',     'addr':0x006A, 'size':2, 'value':0x0000, 'mask':0xFFFF, 'doc':doc.tx_alc_start_delay_help},
              'tx_alc_meas_delay':       {'group':'tx',     'addr':0x006C, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_meas_delay_help},
              'tx_alc_bfrf_gain_max':    {'group':'tx',     'addr':0x006D, 'size':1, 'value':0xFF, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_max_help},
              'tx_alc_bfrf_gain_min':    {'group':'tx',     'addr':0x006E, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_min_help},
              'tx_alc_step_max':         {'group':'tx',     'addr':0x006F, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.tx_alc_step_max_help},
              'tx_alc_pdet_lo_th':       {'group':'tx',     'addr':0x0070, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_pdet_lo_th_help},
              'tx_alc_pdet_hi_offs_th':  {'group':'tx',     'addr':0x0071, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.tx_alc_pdet_hi_offs_th_help},
              'tx_alc_bfrf_gain':        {'group':'tx',     'addr':0x0072, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_help},
              'tx_alc_pdet':             {'group':'tx',     'addr':0x0073, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.tx_alc_pdet_help},
              #
              'adc_ctrl':                {'group':'adc',    'addr':0x0080, 'size':1, 'value':0x00, 'mask':0xB7, 'doc':doc.adc_ctrl_help},
              'adc_clk_div':             {'group':'adc',    'addr':0x0081, 'size':1, 'value':0x03, 'mask':0xFF, 'doc':doc.adc_clk_div_help},
              'adc_sample_cycle':        {'group':'adc',    'addr':0x0082, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.adc_sample_cycle_help},
              'adc_num_samples':         {'group':'adc',    'addr':0x0083, 'size':1, 'value':0x00, 'mask':0x0F, 'doc':doc.adc_num_samples_help}, 
              'adc_sample':              {'group':'adc',    'addr':0x0090, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_sample_help},
              'adc_mean':                {'group':'adc',    'addr':0x0092, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_mean_help},
              'adc_max':                 {'group':'adc',    'addr':0x0094, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_max_help},
              'adc_min':                 {'group':'adc',    'addr':0x0096, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_min_help},
              'adc_diff':                {'group':'adc',    'addr':0x0098, 'size':2, 'value':0x0000, 'mask':0x1FFF, 'doc':doc.adc_diff_help},
              #
              'vco_en':                  {'group':'vco',    'addr':0x00A0, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.vco_en_help},
              'vco_dig_tune':            {'group':'vco',    'addr':0x00A1, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.vco_dig_tune_help},
              'vco_ibias':               {'group':'vco',    'addr':0x00A2, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.vco_ibias_help},
              'vco_vtune_ctrl':          {'group':'vco',    'addr':0x00A3, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.vco_vtune_ctrl_help},
              'vco_vtune_atc_lo_th':     {'group':'vco',    'addr':0x00A4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_atc_lo_th_help},
              'vco_amux_ctrl':           {'group':'vco',    'addr':0x00A5, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.vco_amux_ctrl_help},
              'vco_vtune_th':            {'group':'vco',    'addr':0x00A6, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_th_help},
              'vco_atc_hi_th':           {'group':'vco',    'addr':0x00A7, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_atc_hi_th_help},
              'vco_atc_lo_th':           {'group':'vco',    'addr':0x00A8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_atc_lo_th_help},
              'vco_alc_hi_th':           {'group':'vco',    'addr':0x00A9, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_alc_hi_th_help},
              'vco_override_ctrl':       {'group':'vco',    'addr':0x00AA, 'size':2, 'value':0x00, 'mask':0x01FF, 'doc':doc.vco_override_ctrl_help},
              'vco_alc_del':             {'group':'vco',    'addr':0x00AC, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_alc_del_help},
              'vco_vtune_del':           {'group':'vco',    'addr':0x00AD, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_del_help},
              'vco_tune_loop_del':       {'group':'vco',    'addr':0x00AE, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_tune_loop_del_help},
              'vco_atc_vtune_set_del':   {'group':'vco',    'addr':0x00B1, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_atc_vtune_set_del_help},
              'vco_atc_vtune_unset_del': {'group':'vco',    'addr':0x00B4, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_atc_vtune_unset_del_help},
              'vco_tune_ctrl':           {'group':'vco',    'addr':0x00B7, 'size':1, 'value':0x00, 'mask':0x77, 'doc':doc.vco_tune_ctrl_help},
              'vco_tune_status':         {'group':'vco',    'addr':0x00B8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_tune_status_help},
              'vco_tune_det_status':     {'group':'vco',    'addr':0x00B9, 'size':1, 'value':0x00, 'mask':0x0F, 'doc':doc.vco_tune_det_status_help},
              'vco_tune_freq_cnt':       {'group':'vco',    'addr':0x00BA, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.vco_tune_freq_cnt_help},
              'vco_tune_dig_tune':       {'group':'vco',    'addr':0x00BC, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.vco_tune_dig_tune_help},
              'vco_tune_ibias':          {'group':'vco',    'addr':0x00BD, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.vco_tune_ibias_help},
              'vco_tune_vtune':          {'group':'vco',    'addr':0x00BE, 'size':1, 'value':0x80, 'mask':0xFF, 'doc':doc.vco_tune_vtune_help},
              'vco_tune_fd_polarity':    {'group':'vco',    'addr':0x00BF, 'size':1, 'value':0x01, 'mask':0x01, 'doc':doc.vco_tune_fd_polarity_help},
              #
              'rx_gain_ctrl_mode':       {'group':'rx',     'addr':0x00C0, 'size':1, 'value':0x00, 'mask':0x3B, 'doc':doc.rx_gain_ctrl_mode_help},
              'rx_gain_ctrl_reg_index':  {'group':'rx',     'addr':0x00C1, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_reg_index_help},
              'rx_gain_ctrl_sel':        {'group':'rx',     'addr':0x00C2, 'size':2, 'value':0x0000, 'mask':0x03FF, 'doc':doc.rx_gain_ctrl_sel_help},
              'rx_gain_ctrl_bfrf':       {'group':'rx',     'addr':0x00C4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bfrf_help},
              'rx_gain_ctrl_bb1':        {'group':'rx',     'addr':0x00C5, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb1_help},
              'rx_gain_ctrl_bb2':        {'group':'rx',     'addr':0x00C6, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb2_help},
              'rx_gain_ctrl_bb3':        {'group':'rx',     'addr':0x00C7, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb3_help},
              'rx_bb_q_dco':             {'group':'rx',     'addr':0x00C8, 'size':2, 'value':0x40, 'mask':0x3FFF, 'doc':doc.rx_bb_q_dco_help},
              'rx_bb_i_dco':             {'group':'rx',     'addr':0x00CA, 'size':2, 'value':0x40, 'mask':0x3FFF, 'doc':doc.rx_bb_i_dco_help},
              'rx_dco_en':               {'group':'rx',     'addr':0x00CC, 'size':1, 'value':0x00, 'mask':0x01, 'doc':doc.rx_dco_en_help},
              'rx_bb_biastrim':          {'group':'rx',     'addr':0x00CD, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.rx_bb_biastrim_help},
              'rx_bb_test_ctrl':         {'group':'rx',     'addr':0x00CE, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_bb_test_ctrl_help},
              #
              'agc_int_ctrl':            {'group':'agc',    'addr':0x00E0, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.agc_int_ctrl_help},
              'agc_int_en_ctrl':         {'group':'agc',    'addr':0x00E1, 'size':1, 'value':0x20, 'mask':0x1F, 'doc':doc.agc_int_en_ctrl_help},
              'agc_int_backoff':         {'group':'agc',    'addr':0x00E2, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_backoff_help},
              'agc_int_start_del':       {'group':'agc',    'addr':0x00E3, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_start_del_help},
              'agc_int_timeout':         {'group':'agc',    'addr':0x00E4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_timeout_help},
              'agc_int_gain_change_del': {'group':'agc',    'addr':0x00E5, 'size':1, 'value':0x05, 'mask':0x0F, 'doc':doc.agc_int_gain_change_del_help},
              'agc_int_pdet_en':         {'group':'agc',    'addr':0x00E6, 'size':1, 'value':0x09, 'mask':0x0F, 'doc':doc.agc_int_pdet_en_help},
              'agc_int_pdet_filt':       {'group':'agc',    'addr':0x00E7, 'size':2, 'value':0x1F1F, 'mask':0x1FFF, 'doc':doc.agc_int_pdet_filt_help},
              'agc_int_pdet_th':         {'group':'agc',    'addr':0x00E9, 'size':5, 'value':0x0000000000, 'mask':0xFFFFFFFFFF, 'doc':doc.agc_int_pdet_th_help},
              'agc_int_bfrf_gain_lvl':   {'group':'agc',    'addr':0x00EE, 'size':4, 'value':0xFFCC9966, 'mask':0xFFFFFFFF, 'doc':doc.agc_int_bfrf_gain_lvl_help},
              'agc_int_bb3_gain_lvl':    {'group':'agc',    'addr':0x00F2, 'size':3, 'value':0xFCA752, 'mask':0xFFFFFF, 'doc':doc.agc_int_bb3_gain_lvl_help},
              'agc_int_status_pdet':     {'group':'agc',    'addr':0x00F5, 'size':2, 'value':0xF4, 'mask':0x1FFF, 'doc':doc.agc_int_status_pdet_help},
              'agc_int_status':          {'group':'agc',    'addr':0x00F7, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.agc_int_status_help},
              'agc_int_gain':            {'group':'agc',    'addr':0x00F8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_gain_help},
              'agc_int_gain_setting':    {'group':'agc',    'addr':0x00F9, 'size':4, 'value':0xFFFFFFFF, 'mask':0xFFFFFFFF, 'doc':doc.agc_int_gain_setting_help},
              'agc_ext_ctrl':            {'group':'agc',    'addr':0x00FD, 'size':1, 'value':0x05, 'mask':0x07, 'doc':doc.agc_ext_ctrl_help},

              #
              'trx_ctrl':                {'group':'trx',    'addr':0x01C0, 'size':1, 'value':0x00, 'mask':0x3B, 'doc':doc.trx_ctrl_help},
              'trx_soft_ctrl':           {'group':'trx',    'addr':0x01C1, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.trx_soft_ctrl_help},
              'trx_soft_delay':          {'group':'trx',    'addr':0x01C2, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.trx_soft_delay_help},
              'trx_soft_max_state':      {'group':'trx',    'addr':0x01C3, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.trx_soft_max_state_help},
              'trx_tx_on':               {'group':'trx',    'addr':0x01C4, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF, 'doc':doc.trx_tx_on_help},
              'trx_tx_off':              {'group':'trx',    'addr':0x01C7, 'size':3, 'value':0x00, 'mask':0x1FFFFF, 'doc':doc.trx_tx_off_help},
              'trx_rx_on':               {'group':'trx',    'addr':0x01CA, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF, 'doc':doc.trx_rx_on_help},
              'trx_rx_off':              {'group':'trx',    'addr':0x01CD, 'size':3, 'value':0x00, 'mask':0x1FFFFF, 'doc':doc.trx_rx_off_help},
              'trx_soft_tx_on_enables':  {'group':'trx',    'addr':0x01E0, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F, 'doc':doc.trx_soft_tx_on_enables_help},
              'trx_soft_rx_on_enables':  {'group':'trx',    'addr':0x01E8, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F, 'doc':doc.trx_soft_rx_on_enables_help},
              'trx_soft_bf_on_grp_sel':  {'group':'trx',    'addr':0x01F0, 'size':4, 'value':0x00, 'mask':0xFFFFFFFF, 'doc':doc.trx_soft_bf_on_grp_sel_help}
           }

    regs_mmf =   {'chip_id':                 {'group':'system', 'addr':0x0000, 'size':4, 'value':0x02731803, 'mask':0xFFFFFFFF, 'doc':doc.chip_id_help},
                  'chip_id_sw_en':           {'group':'system', 'addr':0x0004, 'size':1, 'value':0x00, 'mask':0x01, 'doc':doc.chip_id_sw_en_help},
                  'fast_clk_ctrl':           {'group':'system', 'addr':0x0005, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.fast_clk_ctrl_help},
                  'gpio_tx_rx_sw_ctrl':      {'group':'system', 'addr':0x0006, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_tx_rx_sw_ctrl_help},
                  'gpio_agc_rst_ctrl':       {'group':'system', 'addr':0x0007, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_agc_rst_ctrl_help},
                  'gpio_agc_start_ctrl':     {'group':'system', 'addr':0x0008, 'size':1, 'value':0x00, 'mask':0x13, 'doc':doc.gpio_agc_start_ctrl_help},
                  'gpio_agc_gain_in_ctrl':   {'group':'system', 'addr':0x0009, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.gpio_agc_gain_in_ctrl_help},
                  'gpio_agc_gain_out_ctrl':  {'group':'system', 'addr':0x000a, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.gpio_agc_gain_out_ctrl_help},
                  'bist_amux_ctrl':          {'group':'system', 'addr':0x000b, 'size':1, 'value':0x00, 'mask':0xCF, 'doc':doc.bist_amux_ctrl_help},
                  'bist_ot_ctrl':            {'group':'system', 'addr':0x000d, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.bist_ot_ctrl_help},
                  'bist_ot_temp':            {'group':'system', 'addr':0x000e, 'size':1, 'value':0x80, 'mask':0xDF, 'doc':doc.bist_ot_temp_help},
                  'bist_ot_rx_off_mask':     {'group':'system', 'addr':0x000f, 'size':3, 'value':0x000000, 'mask':0x1FFFFF, 'doc':doc.bist_ot_rx_off_mask_help},
                  'bist_ot_tx_off_mask':     {'group':'system', 'addr':0x0012, 'size':3, 'value':0x000000, 'mask':0x1FFFFF, 'doc':doc.bist_ot_tx_off_mask_help},
              #
                  'bias_ctrl':               {'group':'bias',   'addr':0x0020, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.bias_ctrl_help},
                  'bias_vco_x3':             {'group':'bias',   'addr':0x0021, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.bias_vco_x3_help},
                  'bias_pll':                {'group':'bias',   'addr':0x0022, 'size':1, 'value':0x00, 'mask':0x37, 'doc':doc.bias_pll_help},
                  'bias_lo':                 {'group':'bias',   'addr':0x0023, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.bias_lo_help},
                  'bias_tx':                 {'group':'bias',   'addr':0x0024, 'size':2, 'value':0x0000, 'mask':0xFFFF, 'doc':doc.bias_tx_help},
                  'bias_rx':                 {'group':'bias',   'addr':0x0026, 'size':2, 'value':0x0000, 'mask':0x0FFF, 'doc':doc.bias_rx_help},
              #
                  'pll_en':                  {'group':'pll',    'addr':0x0040, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.pll_en_help},
                  'pll_divn':                {'group':'pll',    'addr':0x0041, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.pll_divn_help},
                  'pll_pfd':                 {'group':'pll',    'addr':0x0042, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.pll_pfd_help},
                  'pll_chp':                 {'group':'pll',    'addr':0x0043, 'size':1, 'value':0x00, 'mask':0x73, 'doc':doc.pll_chp_help},
                  'pll_ld_mux_ctrl':         {'group':'pll',    'addr':0x0044, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.pll_ld_mux_ctrl_help},
                  'pll_test_mux_in':         {'group':'pll',    'addr':0x0045, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.pll_test_mux_in_help},
                  'pll_ref_in_lvds_en':      {'group':'pll',    'addr':0x0046, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.pll_ref_in_lvds_en_help},
              #
                  'tx_ctrl':                 {'group':'tx',     'addr':0x0060, 'size':1, 'value':0x10, 'mask':0x7F, 'doc':doc.tx_ctrl_help},
                  'tx_bb_q_dco':             {'group':'tx',     'addr':0x0061, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.tx_bb_q_dco_help},
                  'tx_bb_i_dco':             {'group':'tx',     'addr':0x0062, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.tx_bb_i_dco_help},
                  'tx_bb_phase':             {'group':'tx',     'addr':0x0063, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.tx_bb_phase_help},
                  'tx_bb_gain':              {'group':'tx',     'addr':0x0064, 'size':1, 'value':0x00, 'mask':0x23, 'doc':doc.tx_bb_gain_help},
                  'tx_bb_iq_gain':           {'group':'tx',     'addr':0x0065, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_bb_iq_gain_help},
                  'tx_bfrf_gain':            {'group':'tx',     'addr':0x0066, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_bfrf_gain_help},
                  'tx_bf_pdet_mux':          {'group':'tx',     'addr':0x0067, 'size':1, 'value':0x00, 'mask':0xBF, 'doc':doc.tx_bf_pdet_mux_help},
                  'tx_alc_ctrl':             {'group':'tx',     'addr':0x0068, 'size':1, 'value':0x00, 'mask':0xF3, 'doc':doc.tx_alc_ctrl_help},
                  'tx_alc_loop_cnt':         {'group':'tx',     'addr':0x0069, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_loop_cnt_help},
                  'tx_alc_start_delay':      {'group':'tx',     'addr':0x006A, 'size':2, 'value':0x0000, 'mask':0xFFFF, 'doc':doc.tx_alc_start_delay_help},
                  'tx_alc_meas_delay':       {'group':'tx',     'addr':0x006C, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_meas_delay_help},
                  'tx_alc_bfrf_gain_max':    {'group':'tx',     'addr':0x006D, 'size':1, 'value':0xFF, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_max_help},
                  'tx_alc_bfrf_gain_min':    {'group':'tx',     'addr':0x006E, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_min_help},
                  'tx_alc_step_max':         {'group':'tx',     'addr':0x006F, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.tx_alc_step_max_help},
                  'tx_alc_pdet_lo_th':       {'group':'tx',     'addr':0x0070, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_pdet_lo_th_help},
                  'tx_alc_pdet_hi_offs_th':  {'group':'tx',     'addr':0x0071, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.tx_alc_pdet_hi_offs_th_help},
                  'tx_alc_bfrf_gain':        {'group':'tx',     'addr':0x0072, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.tx_alc_bfrf_gain_help},
                  'tx_alc_pdet':             {'group':'tx',     'addr':0x0073, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.tx_alc_pdet_help},
              #
                  'adc_ctrl':                {'group':'adc',    'addr':0x0080, 'size':1, 'value':0x00, 'mask':0xB7, 'doc':doc.adc_ctrl_help},
                  'adc_clk_div':             {'group':'adc',    'addr':0x0081, 'size':1, 'value':0x03, 'mask':0xFF, 'doc':doc.adc_clk_div_help},
                  'adc_sample_cycle':        {'group':'adc',    'addr':0x0082, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.adc_sample_cycle_help},
                  'adc_num_samples':         {'group':'adc',    'addr':0x0083, 'size':1, 'value':0x00, 'mask':0x0F, 'doc':doc.adc_num_samples_help},
                  'adc_sample':              {'group':'adc',    'addr':0x0090, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_sample_help},
                  'adc_mean':                {'group':'adc',    'addr':0x0092, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_mean_help},
                  'adc_max':                 {'group':'adc',    'addr':0x0094, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_max_help},
                  'adc_min':                 {'group':'adc',    'addr':0x0096, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.adc_min_help},
                  'adc_diff':                {'group':'adc',    'addr':0x0098, 'size':2, 'value':0x0000, 'mask':0x1FFF, 'doc':doc.adc_diff_help},
              #
                  'vco_en':                  {'group':'vco',    'addr':0x00A0, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.vco_en_help},
                  'vco_dig_tune':            {'group':'vco',    'addr':0x00A1, 'size':1, 'value':0x00, 'mask':0x7F, 'doc':doc.vco_dig_tune_help},
                  'vco_ibias':               {'group':'vco',    'addr':0x00A2, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.vco_ibias_help},
                  'vco_vtune_ctrl':          {'group':'vco',    'addr':0x00A3, 'size':1, 'value':0x00, 'mask':0x33, 'doc':doc.vco_vtune_ctrl_help},
                  'vco_vtune_atc_lo_th':     {'group':'vco',    'addr':0x00A4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_atc_lo_th_help},
                  'vco_amux_ctrl':           {'group':'vco',    'addr':0x00A5, 'size':1, 'value':0x00, 'mask':0x1F, 'doc':doc.vco_amux_ctrl_help},
                  'vco_vtune_th':            {'group':'vco',    'addr':0x00A6, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_th_help},
                  'vco_atc_hi_th':           {'group':'vco',    'addr':0x00A7, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_atc_hi_th_help},
                  'vco_atc_lo_th':           {'group':'vco',    'addr':0x00A8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_atc_lo_th_help},
                  'vco_alc_hi_th':           {'group':'vco',    'addr':0x00A9, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_alc_hi_th_help},
                  'vco_override_ctrl':       {'group':'vco',    'addr':0x00AA, 'size':2, 'value':0x00, 'mask':0x01FF, 'doc':doc.vco_override_ctrl_help},
                  'vco_alc_del':             {'group':'vco',    'addr':0x00AC, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_alc_del_help},
                  'vco_vtune_del':           {'group':'vco',    'addr':0x00AD, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_vtune_del_help},
                  'vco_tune_loop_del':       {'group':'vco',    'addr':0x00AE, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_tune_loop_del_help},
                  'vco_atc_vtune_set_del':   {'group':'vco',    'addr':0x00B1, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_atc_vtune_set_del_help},
                  'vco_atc_vtune_unset_del': {'group':'vco',    'addr':0x00B4, 'size':3, 'value':0x00, 'mask':0x03FFFF, 'doc':doc.vco_atc_vtune_unset_del_help},
                  'vco_tune_ctrl':           {'group':'vco',    'addr':0x00B7, 'size':1, 'value':0x00, 'mask':0x77, 'doc':doc.vco_tune_ctrl_help},
                  'vco_tune_status':         {'group':'vco',    'addr':0x00B8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.vco_tune_status_help},
                  'vco_tune_det_status':     {'group':'vco',    'addr':0x00B9, 'size':1, 'value':0x00, 'mask':0x0F, 'doc':doc.vco_tune_det_status_help},
                  'vco_tune_freq_cnt':       {'group':'vco',    'addr':0x00BA, 'size':2, 'value':0x000, 'mask':0x0FFF, 'doc':doc.vco_tune_freq_cnt_help},
                  'vco_tune_dig_tune':       {'group':'vco',    'addr':0x00BC, 'size':1, 'value':0x40, 'mask':0x7F, 'doc':doc.vco_tune_dig_tune_help},
                  'vco_tune_ibias':          {'group':'vco',    'addr':0x00BD, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.vco_tune_ibias_help},
                  'vco_tune_vtune':          {'group':'vco',    'addr':0x00BE, 'size':1, 'value':0x80, 'mask':0xFF, 'doc':doc.vco_tune_vtune_help},
                  'vco_tune_fd_polarity':    {'group':'vco',    'addr':0x00BF, 'size':1, 'value':0x01, 'mask':0x01, 'doc':doc.vco_tune_fd_polarity_help},
              #
                  'rx_gain_ctrl_mode':       {'group':'rx',     'addr':0x00C0, 'size':1, 'value':0x00, 'mask':0x3B, 'doc':doc.rx_gain_ctrl_mode_help},
                  'rx_gain_ctrl_reg_index':  {'group':'rx',     'addr':0x00C1, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_reg_index_help},
                  'rx_gain_ctrl_sel':        {'group':'rx',     'addr':0x00C2, 'size':2, 'value':0x0000, 'mask':0x03FF, 'doc':doc.rx_gain_ctrl_sel_help},
                  'rx_gain_ctrl_bfrf':       {'group':'rx',     'addr':0x00C4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bfrf_help},
                  'rx_gain_ctrl_bb1':        {'group':'rx',     'addr':0x00C5, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb1_help},
                  'rx_gain_ctrl_bb2':        {'group':'rx',     'addr':0x00C6, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb2_help},
                  'rx_gain_ctrl_bb3':        {'group':'rx',     'addr':0x00C7, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_gain_ctrl_bb3_help},
                  'rx_bb_q_dco':             {'group':'rx',     'addr':0x00C8, 'size':2, 'value':0x40, 'mask':0x3FFF, 'doc':doc.rx_bb_q_dco_help},
                  'rx_bb_i_dco':             {'group':'rx',     'addr':0x00CA, 'size':2, 'value':0x40, 'mask':0x3FFF, 'doc':doc.rx_bb_i_dco_help},
                  'rx_dco_en':               {'group':'rx',     'addr':0x00CC, 'size':1, 'value':0x00, 'mask':0x01, 'doc':doc.rx_dco_en_help},
                  'rx_drv_dco':              {'group':'rx',     'addr':0x001C, 'size':4, 'value':0xFF0000FF, 'mask':0xFFFFFFFF, 'doc':doc.rx_drv_dco_help},
                  'rx_bb_biastrim':          {'group':'rx',     'addr':0x00CD, 'size':1, 'value':0x00, 'mask':0x3F, 'doc':doc.rx_bb_biastrim_help},
                  'rx_bb_test_ctrl':         {'group':'rx',     'addr':0x00CE, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.rx_bb_test_ctrl_help},
              #
                  'agc_int_ctrl':            {'group':'agc',    'addr':0x00E0, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.agc_int_ctrl_help},
                  'agc_int_en_ctrl':         {'group':'agc',    'addr':0x00E1, 'size':1, 'value':0x20, 'mask':0x1F, 'doc':doc.agc_int_en_ctrl_help},
                  'agc_int_backoff':         {'group':'agc',    'addr':0x00E2, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_backoff_help},
                  'agc_int_start_del':       {'group':'agc',    'addr':0x00E3, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_start_del_help},
                  'agc_int_timeout':         {'group':'agc',    'addr':0x00E4, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_timeout_help},
                  'agc_int_gain_change_del': {'group':'agc',    'addr':0x00E5, 'size':1, 'value':0x05, 'mask':0x0F, 'doc':doc.agc_int_gain_change_del_help},
                  'agc_int_pdet_en':         {'group':'agc',    'addr':0x00E6, 'size':1, 'value':0x09, 'mask':0x0F, 'doc':doc.agc_int_pdet_en_help},
                  'agc_int_pdet_filt':       {'group':'agc',    'addr':0x00E7, 'size':2, 'value':0x1F1F, 'mask':0x1FFF, 'doc':doc.agc_int_pdet_filt_help},
                  'agc_int_pdet_th':         {'group':'agc',    'addr':0x00E9, 'size':5, 'value':0x0000000000, 'mask':0xFFFFFFFFFF, 'doc':doc.agc_int_pdet_th_help},
                  'agc_int_bfrf_gain_lvl':   {'group':'agc',    'addr':0x00EE, 'size':4, 'value':0xFFCC9966, 'mask':0xFFFFFFFF, 'doc':doc.agc_int_bfrf_gain_lvl_help},
                  'agc_int_bb3_gain_lvl':    {'group':'agc',    'addr':0x00F2, 'size':3, 'value':0xFCA752, 'mask':0xFFFFFF, 'doc':doc.agc_int_bb3_gain_lvl_help},
                  'agc_int_status_pdet':     {'group':'agc',    'addr':0x00F5, 'size':2, 'value':0xF4, 'mask':0x1FFF, 'doc':doc.agc_int_status_pdet_help},
                  'agc_int_status':          {'group':'agc',    'addr':0x00F7, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.agc_int_status_help},
                  'agc_int_gain':            {'group':'agc',    'addr':0x00F8, 'size':1, 'value':0x00, 'mask':0xFF, 'doc':doc.agc_int_gain_help},
                  'agc_int_gain_setting':    {'group':'agc',    'addr':0x00F9, 'size':4, 'value':0xFFFFFFFF, 'mask':0xFFFFFFFF, 'doc':doc.agc_int_gain_setting_help},
                  'agc_ext_ctrl':            {'group':'agc',    'addr':0x00FD, 'size':1, 'value':0x05, 'mask':0x07, 'doc':doc.agc_ext_ctrl_help},

              #
                  'trx_ctrl':                {'group':'trx',    'addr':0x01C0, 'size':1, 'value':0x00, 'mask':0x3B, 'doc':doc.trx_ctrl_help},
                  'trx_soft_ctrl':           {'group':'trx',    'addr':0x01C1, 'size':1, 'value':0x00, 'mask':0x03, 'doc':doc.trx_soft_ctrl_help},
                  'trx_soft_delay':          {'group':'trx',    'addr':0x01C2, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.trx_soft_delay_help},
                  'trx_soft_max_state':      {'group':'trx',    'addr':0x01C3, 'size':1, 'value':0x00, 'mask':0x07, 'doc':doc.trx_soft_max_state_help},
                  'trx_tx_on':               {'group':'trx',    'addr':0x01C4, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF, 'doc':doc.trx_tx_on_help},
                  'trx_tx_off':              {'group':'trx',    'addr':0x01C7, 'size':3, 'value':0x00, 'mask':0x1FFFFF, 'doc':doc.trx_tx_off_help},
                  'trx_rx_on':               {'group':'trx',    'addr':0x01CA, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF, 'doc':doc.trx_rx_on_help},
                  'trx_rx_off':              {'group':'trx',    'addr':0x01CD, 'size':3, 'value':0x00, 'mask':0x1FFFFF, 'doc':doc.trx_rx_off_help},
                  'trx_soft_tx_on_enables':  {'group':'trx',    'addr':0x01E0, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F, 'doc':doc.trx_soft_tx_on_enables_help},
                  'trx_soft_rx_on_enables':  {'group':'trx',    'addr':0x01E8, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F, 'doc':doc.trx_soft_rx_on_enables_help},
                  'trx_soft_bf_on_grp_sel':  {'group':'trx',    'addr':0x01F0, 'size':4, 'value':0x00, 'mask':0xFFFFFFFF, 'doc':doc.trx_soft_bf_on_grp_sel_help}
           }


    def __new__(cls, evkplatform_type='MB1', chip_type=None):
        if chip_type != None:
            if cls.device_info.get_attrib('chip_type') != chip_type:
                cls.device_info.set_attrib('chip_type', chip_type)
                cls.__instance = None
        if cls.__instance is None:
            cls.__instance = super(Register, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, evkplatform_type='MB1', chip_type=None):
        if self.__initialized:
            return
        self.__initialized = True
        self.selected_map = self.regs

        if self.device_info.get_attrib('chip_type') == None:
            ederspi.EderSpi.__init__(self, self.regs, evkplatform_type)
        elif self.device_info.get_attrib('chip_type') == 'Eder B':
            ederspi.EderSpi.__init__(self, self.regs, evkplatform_type)
        elif self.device_info.get_attrib('chip_type') == 'Eder B MMF':
            ederspi.EderSpi.__init__(self, self.regs_mmf, evkplatform_type)
            self.selected_map = self.regs_mmf

    def doc(self, reg_name):
        try:
            print ('')
            print (self.selected_map[reg_name]['doc'])
            print ('')
        except:
            print ('Incorrect register name')


